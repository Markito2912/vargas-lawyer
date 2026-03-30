param(
    [string]$SiteUrl = "sc-domain:vargaslawyer.com",
    [string]$SitemapUrl = "https://vargaslawyer.com/sitemap.xml",
    [string]$ClientSecret = ".\\client_secret.json",
    [switch]$OpenLinks
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

python -m pip install -r .\requirements-gsc.txt

$argsList = @(
    ".\\gsc_post_deploy.py",
    "--site-url", $SiteUrl,
    "--sitemap-url", $SitemapUrl,
    "--client-secret", $ClientSecret
)

if ($OpenLinks) {
    $argsList += "--open-links"
}

python @argsList
