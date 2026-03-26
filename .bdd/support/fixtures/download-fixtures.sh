#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"

download() {
    local name="$1" url="$2" output="$3"
    printf "  %-16s" "$name..."
    if curl -sfL "$url" -o "$DIR/$output"; then
        echo "✓"
    else
        echo "✗"
        return 1
    fi
}

echo "Downloading test fixture specs..."
echo

download "Petstore" "https://petstore3.swagger.io/api/v3/openapi.json" "petstore.json"
download "GitHub" "https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/api.github.com/api.github.com.yaml" "github.yaml"
download "Stripe" "https://raw.githubusercontent.com/stripe/openapi/master/openapi/spec3.yaml" "stripe.yaml"
download "Spotify" "https://raw.githubusercontent.com/sonallux/spotify-web-api/main/official-spotify-open-api.yml" "spotify.yaml"
download "Cloudflare" "https://raw.githubusercontent.com/cloudflare/api-schemas/main/openapi.yaml" "cloudflare.yaml"
download "SendGrid" "https://raw.githubusercontent.com/twilio/sendgrid-oai/main/spec/yaml/tsg_mail_v3.yaml" "sendgrid.yaml"
download "GitLab" "https://gitlab.com/gitlab-org/gitlab/-/raw/master/doc/api/openapi/openapi_v2.yaml" "gitlab.yaml"
download "Netlify" "https://open-api.netlify.com/swagger.json" "netlify.json"
download "PagerDuty" "https://raw.githubusercontent.com/PagerDuty/api-schema/main/reference/REST/openapiv3.json" "pagerduty.json"
download "httpbin" "https://httpbin.org/spec.json" "httpbin.json"

echo
echo "Supplemental"
download "DigitalOcean" "https://api-engineering.nyc3.digitaloceanspaces.com/spec-ci/DigitalOcean-public.v2.yaml" "digitalocean.yaml"
download "Slack" "https://raw.githubusercontent.com/slackapi/slack-api-specs/master/web-api/slack_web_openapi_v2.json" "slack.json"

echo
echo "Done."
