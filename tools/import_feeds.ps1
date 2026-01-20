param(
  [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot ".."))
)

$ErrorActionPreference = "Stop"

function Guess-Language {
  param([string]$Name, [string]$Url)
  if ($Name -match "\p{IsArabic}") { return "ar" }
  if ($Url -match "(aitnews|arabhardware|almalnews|tech-wd|arageek|raqami|wamda|egyptianstreets)" ) { return "ar" }
  return "en"
}

function Guess-Category {
  param([string]$Hint, [string]$Url)
  $hintText = if ($Hint) { $Hint } else { "" }
  $urlText = if ($Url) { $Url } else { "" }
  $h = (($hintText + " " + $urlText).ToLowerInvariant())

  if ($h -match "cyber|security|hacker|infosec|malware|breach") { return "cyber" }
  if ($h -match "ai|artificial|machine|ml|deepmind|openai|arxiv|llm") { return "ai" }
  if ($h -match "program|developer|devops|python|javascript|kubernetes|docker|cloud|engineering") { return "programming" }
  if ($h -match "startup|venture|business|economy|finance|mckinsey|wef|hbr|ft|bloomberg") { return "business" }
  if ($h -match "iot|hardware|chip|semiconductor|raspberry|arduino") { return "tech" }
  return "tech"
}

function Normalize-Category {
  param([string]$Cat)
  # Map to FeedCategory enum values
  switch ($Cat) {
    "cyber" { return "news" } # no explicit cyber enum; treat as news
    default {
      $c = ($(if ($Cat) { $Cat } else { "other" })).ToLowerInvariant()
      if ($c -in @("tech","business","ai","programming","news","lifestyle","education","other")) { return $c }
      return "other"
    }
  }
}

function New-FeedObject {
  param(
    [string]$Id,
    [string]$Name,
    [string]$Url,
    [string]$Category,
    [string]$Language,
    [bool]$IsActive,
    [int]$Priority
  )

  [pscustomobject]@{
    id = $Id
    name = $Name
    url = $Url
    category = $Category
    language = $Language
    is_active = $IsActive
    priority = $Priority
    last_fetched = $null
    created_at = (Get-Date).ToUniversalTime().ToString("o")
  }
}

function Save-JsonUtf8 {
  param(
    [string]$Path,
    [object]$Data
  )

  $json = $Data | ConvertTo-Json -Depth 20
  # PowerShell 5.1: use UTF8 without BOM
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $json + "`n", $utf8NoBom)
}

$feedsPath = Join-Path $Root "data\feeds.json"
$opmlPath  = Join-Path $Root "data\feeds.opml"
$docxList  = Join-Path $Root "data\feeds_import\urls_from_docx.txt"

$script:feeds = @()
if (Test-Path $feedsPath) {
  try {
    $script:feeds = (Get-Content $feedsPath -Raw | ConvertFrom-Json)
  } catch {
    Write-Warning "Failed to parse feeds.json; starting fresh. $_"
    $script:feeds = @()
  }
}

$script:existing = @{}
foreach ($f in $script:feeds) {
  if ($null -ne $f.url) {
    $script:existing[$f.url.ToString().Trim().ToLowerInvariant()] = $true
  }
}

function Add-Feed {
  param(
    [string]$Name,
    [string]$Url,
    [string]$CategoryHint,
    [bool]$Active = $true,
    [int]$Priority = 5
  )

  if ([string]::IsNullOrWhiteSpace($Url)) { return }

  $u = $Url.Trim()
  $u = $u.TrimEnd(@('.',',',';','"',')',']'))
  if ($u -notmatch '^https?://') { $u = "https://$u" }

  # Skip obvious non-feeds / placeholders
  if ($u -match '^https?://rss\.app/?$' -or $u -match '^https?://RSS\.app/?$') { return }

  $key = $u.ToLowerInvariant()
  if ($script:existing.ContainsKey($key)) { return }

  $lang = Guess-Language -Name $Name -Url $u
  $cat  = Normalize-Category (Guess-Category -Hint $CategoryHint -Url $u)

  $id = "feed_${lang}_$([int]($script:feeds.Count + 1))"
  if ([string]::IsNullOrWhiteSpace($Name)) {
    try { $finalName = ([uri]$u).Host } catch { $finalName = $u }
  } else {
    $finalName = $Name.Trim()
  }

  $script:feeds += (New-FeedObject -Id $id -Name $finalName -Url $u -Category $cat -Language $lang -IsActive:$Active -Priority $Priority)
  $script:existing[$key] = $true
}

# 1) OPML feeds
if (Test-Path $opmlPath) {
  [xml]$opml = Get-Content -Path $opmlPath -Raw
  $nodes = $opml.SelectNodes("//outline[@xmlUrl]")
  foreach ($n in $nodes) {
    $title = $n.GetAttribute("title")
    if ([string]::IsNullOrWhiteSpace($title)) { $title = $n.GetAttribute("text") }
    $xmlUrl = $n.GetAttribute("xmlUrl")

    $parent = $n.ParentNode
    $hint = ""
    if ($parent -and $parent.Attributes -and $parent.Attributes["title"]) {
      $hint = $parent.Attributes["title"].Value
    }

    Add-Feed -Name $title -Url $xmlUrl -CategoryHint $hint -Active $true -Priority 5
  }
}

# 2) DOCX extracted URLs
if (Test-Path $docxList) {
  $docxUrls = Get-Content -Path $docxList | Where-Object { $_ -and $_.Trim() -ne "" }
  foreach ($u in $docxUrls) {
    Add-Feed -Name "" -Url $u -CategoryHint "docx" -Active $true -Priority 4
  }
}

# 3) Curated extras (to reach 100+ diversified sources)
$extras = @(
  @{ name = "Engadget"; url = "https://www.engadget.com/rss.xml"; hint = "tech" },
  @{ name = "VentureBeat"; url = "https://venturebeat.com/feed/"; hint = "ai business" },
  @{ name = "Ars Technica (already in OPML, safe dup)"; url = "https://arstechnica.com/feed/"; hint = "tech" },
  @{ name = "Wired (Tech)"; url = "https://www.wired.com/feed/rss"; hint = "tech" },
  @{ name = "The Register - Security"; url = "https://www.theregister.com/security/headlines.atom"; hint = "security" },
  @{ name = "BleepingComputer"; url = "https://www.bleepingcomputer.com/feed/"; hint = "security" },
  @{ name = "Schneier on Security"; url = "https://www.schneier.com/feed/atom/"; hint = "security" },
  @{ name = "SecurityWeek"; url = "https://www.securityweek.com/feed/"; hint = "security" },
  @{ name = "Help Net Security"; url = "https://www.helpnetsecurity.com/feed/"; hint = "security" },
  @{ name = "InfoQ"; url = "https://www.infoq.com/feed/"; hint = "programming" },
  @{ name = "Stack Overflow Blog"; url = "https://stackoverflow.blog/feed/"; hint = "programming" },
  @{ name = "GitHub Blog"; url = "https://github.blog/feed/"; hint = "programming" },
  @{ name = "Microsoft DevBlogs"; url = "https://devblogs.microsoft.com/feed/"; hint = "programming" },
  @{ name = "AWS News Blog"; url = "https://aws.amazon.com/blogs/aws/feed/"; hint = "cloud programming" },
  @{ name = "Google Cloud Blog"; url = "https://cloud.google.com/blog/rss/"; hint = "cloud" },
  @{ name = "Cloudflare Blog"; url = "https://blog.cloudflare.com/rss/"; hint = "security cloud" },
  @{ name = "Kubernetes Blog"; url = "https://kubernetes.io/feed.xml"; hint = "kubernetes" },
  @{ name = "Docker Blog"; url = "https://www.docker.com/blog/feed/"; hint = "docker" },
  @{ name = "web.dev"; url = "https://web.dev/feed.xml"; hint = "programming" },
  @{ name = "Chrome Developers"; url = "https://developer.chrome.com/blog/feed.xml"; hint = "programming" },
  @{ name = "Smashing Magazine"; url = "https://www.smashingmagazine.com/feed/"; hint = "programming" },
  @{ name = "Mozilla Hacks"; url = "https://hacks.mozilla.org/feed/"; hint = "programming" },
  @{ name = "Python Software Foundation"; url = "https://pyfound.blogspot.com/feeds/posts/default?alt=rss"; hint = "python" },
  @{ name = "Real Python"; url = "https://realpython.com/atom.xml"; hint = "python" },
  @{ name = "JetBrains Blog"; url = "https://blog.jetbrains.com/feed/"; hint = "programming" },
  @{ name = "Netflix TechBlog"; url = "https://netflixtechblog.com/feed"; hint = "engineering" },
  @{ name = "Meta Engineering"; url = "https://engineering.fb.com/feed/"; hint = "engineering" },
  @{ name = "OpenAI (dup safe)"; url = "https://openai.com/feed"; hint = "ai" },
  @{ name = "DeepMind (dup safe)"; url = "https://deepmind.google/blog/rss.xml"; hint = "ai" },
  @{ name = "Hugging Face Blog"; url = "https://huggingface.co/blog/feed.xml"; hint = "ai" },
  @{ name = "Papers with Code Blog"; url = "https://blog.paperswithcode.com/rss/"; hint = "ai" },
  @{ name = "arXiv cs.AI"; url = "https://export.arxiv.org/rss/cs.AI"; hint = "ai research" },
  @{ name = "arXiv cs.LG"; url = "https://export.arxiv.org/rss/cs.LG"; hint = "ai research" },
  @{ name = "arXiv cs.CL"; url = "https://export.arxiv.org/rss/cs.CL"; hint = "ai research" },
  @{ name = "arXiv stat.ML"; url = "https://export.arxiv.org/rss/stat.ML"; hint = "ai research" },
  @{ name = "NVIDIA Developer Blog"; url = "https://developer.nvidia.com/blog/feed/"; hint = "ai hardware" },
  @{ name = "Google Research"; url = "https://research.google/blog/rss/"; hint = "ai" },
  @{ name = "Google Developers"; url = "https://developers.googleblog.com/feeds/posts/default?alt=rss"; hint = "programming" },
  @{ name = "Android Developers"; url = "https://android-developers.googleblog.com/feeds/posts/default?alt=rss"; hint = "programming" },
  @{ name = "Raspberry Pi"; url = "https://www.raspberrypi.com/news/feed/"; hint = "hardware" },
  @{ name = "IEEE Spectrum"; url = "https://spectrum.ieee.org/rss/fulltext"; hint = "tech" },
  @{ name = "EE Times"; url = "https://www.eetimes.com/feed/"; hint = "hardware" },
  @{ name = "Electronics Weekly"; url = "https://www.electronicsweekly.com/feed/"; hint = "hardware" },
  @{ name = "Slashdot"; url = "https://rss.slashdot.org/Slashdot/slashdotMain"; hint = "tech" },
  @{ name = "DZone"; url = "https://dzone.com/feed"; hint = "programming" },
  @{ name = "InfoWorld"; url = "https://www.infoworld.com/index.rss"; hint = "programming" },
  @{ name = "Computerworld"; url = "https://www.computerworld.com/index.rss"; hint = "tech" },
  @{ name = "Network World"; url = "https://www.networkworld.com/index.rss"; hint = "tech" },
  @{ name = "Fast Company"; url = "https://www.fastcompany.com/rss"; hint = "business tech" },
  @{ name = "The Next Web"; url = "https://thenextweb.com/feed"; hint = "tech" },
  @{ name = "Digital Trends"; url = "https://www.digitaltrends.com/feed/"; hint = "tech" },
  @{ name = "Gizmodo"; url = "https://gizmodo.com/rss"; hint = "tech" },
  @{ name = "ZDNET"; url = "https://www.zdnet.com/news/rss.xml"; hint = "tech" },
  @{ name = "CNET"; url = "https://www.cnet.com/rss/news/"; hint = "tech" },
  @{ name = "TechRadar"; url = "https://www.techradar.com/rss"; hint = "tech" },
  @{ name = "The Information (skip)"; url = ""; hint = "" }
)

foreach ($e in $extras) {
  if ($e.url -and $e.url.Trim() -ne "") {
    Add-Feed -Name $e.name -Url $e.url -CategoryHint $e.hint -Active $true -Priority 4
  }
}

Save-JsonUtf8 -Path $feedsPath -Data $script:feeds

"TOTAL_FEEDS=$($script:feeds.Count)"