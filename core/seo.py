import json
from textwrap import shorten
from urllib.parse import urljoin, urlsplit

from django.conf import settings
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import get_language


def _compact(value):
    """Collapse user-authored whitespace so metadata stays on one line."""
    return " ".join(str(value or "").split())


def _truncate(value, length):
    return shorten(_compact(value), width=length, placeholder="…")


def _public_url(path):
    """Return a stable public URL without trusting the incoming Host header."""
    if not path:
        return ""
    if urlsplit(path).scheme in {"http", "https"}:
        return path
    return urljoin(f"{settings.PUBLIC_SITE_URL.rstrip('/')}/", path.lstrip("/"))


def _safe_json(data):
    """Serialize JSON-LD and prevent user content from closing the script tag."""
    value = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    value = value.replace("<", "\\u003C").replace(">", "\\u003E").replace("&", "\\u0026")
    return mark_safe(value)


def destination_seo(destination):
    """Build localized, unique SEO metadata for a tourist destination page."""
    english = (get_language() or "es").lower().startswith("en")
    language = "en" if english else "es"
    name = _compact(destination.nombre_localizado)
    department = _compact(destination.departamento.nombre)
    country = _compact(destination.departamento.pais.nombre)
    location = ", ".join(part for part in (department, country) if part)
    summary = _compact(destination.resumen_localizado)
    title = f"{name} | SAMI Travels & Tours"

    if english:
        lead = f"Discover {name} in {location}."
        image_alt = f"Travel to {name}, {country}"
        home_label = "Home"
        destinations_label = "Destinations"
    else:
        lead = f"Descubre {name} en {location}."
        image_alt = f"Viajes a {name}, {country}"
        home_label = "Inicio"
        destinations_label = "Destinos"

    description = _truncate(f"{lead} {summary}", 160)
    title = _truncate(title, 65)
    canonical_url = _public_url(
        reverse("core:destination-detail", args=[destination.slug])
    )
    homepage_url = _public_url(reverse("core:portal-publico"))
    image_url = _public_url(destination.imagen.url) if destination.imagen else ""
    destination_id = f"{canonical_url}#destination"
    breadcrumb_id = f"{canonical_url}#breadcrumb"

    destination_schema = {
        "@type": "TouristDestination",
        "@id": destination_id,
        "name": name,
        "description": description,
        "url": canonical_url,
        "containedInPlace": {
            "@type": "AdministrativeArea",
            "name": department,
            "containedInPlace": {"@type": "Country", "name": country},
        },
    }
    if image_url:
        destination_schema["image"] = {
            "@type": "ImageObject",
            "url": image_url,
            "contentUrl": image_url,
            "caption": image_alt,
        }

    structured_data = {
        "@context": "https://schema.org",
        "@graph": [
            destination_schema,
            {
                "@type": "WebPage",
                "@id": f"{canonical_url}#webpage",
                "url": canonical_url,
                "name": title,
                "description": description,
                "inLanguage": language,
                "about": {"@id": destination_id},
                "breadcrumb": {"@id": breadcrumb_id},
            },
            {
                "@type": "BreadcrumbList",
                "@id": breadcrumb_id,
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": home_label,
                        "item": homepage_url,
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": destinations_label,
                        "item": f"{homepage_url}#destinos",
                    },
                    {
                        "@type": "ListItem",
                        "position": 3,
                        "name": name,
                        "item": canonical_url,
                    },
                ],
            },
        ],
    }

    return {
        "title": title,
        "description": description,
        "canonical_url": canonical_url,
        "image_url": image_url,
        "image_alt": image_alt,
        "locale": "en_US" if english else "es_SV",
        "alternate_locale": "es_SV" if english else "en_US",
        "structured_data": _safe_json(structured_data),
    }
