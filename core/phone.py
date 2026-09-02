import re


COUNTRY_CODES = (
    ("+503", "🇸🇻 El Salvador (+503)"),
    ("+1", "🇺🇸 Estados Unidos / Canadá (+1)"),
    ("+502", "🇬🇹 Guatemala (+502)"),
    ("+504", "🇭🇳 Honduras (+504)"),
    ("+505", "🇳🇮 Nicaragua (+505)"),
    ("+506", "🇨🇷 Costa Rica (+506)"),
    ("+507", "🇵🇦 Panamá (+507)"),
    ("+52", "🇲🇽 México (+52)"),
    ("+34", "🇪🇸 España (+34)"),
    ("+57", "🇨🇴 Colombia (+57)"),
    ("+51", "🇵🇪 Perú (+51)"),
    ("+593", "🇪🇨 Ecuador (+593)"),
    ("+56", "🇨🇱 Chile (+56)"),
    ("+54", "🇦🇷 Argentina (+54)"),
    ("+55", "🇧🇷 Brasil (+55)"),
    ("+591", "🇧🇴 Bolivia (+591)"),
    ("+595", "🇵🇾 Paraguay (+595)"),
    ("+598", "🇺🇾 Uruguay (+598)"),
    ("+58", "🇻🇪 Venezuela (+58)"),
    ("+501", "🇧🇿 Belice (+501)"),
    ("+53", "🇨🇺 Cuba (+53)"),
    ("+1809", "🇩🇴 República Dominicana (+1 809)"),
    ("+1876", "🇯🇲 Jamaica (+1 876)"),
    ("+44", "🇬🇧 Reino Unido (+44)"),
    ("+33", "🇫🇷 Francia (+33)"),
    ("+49", "🇩🇪 Alemania (+49)"),
    ("+39", "🇮🇹 Italia (+39)"),
    ("+351", "🇵🇹 Portugal (+351)"),
    ("+31", "🇳🇱 Países Bajos (+31)"),
)

COUNTRY_CODE_VALUES = tuple(code for code, _label in COUNTRY_CODES)


def normalize_international_phone(country_code, national_number):
    """Return a readable international number or raise ValueError."""
    code = (country_code or "").strip().replace(" ", "")
    number = (national_number or "").strip()
    if not number:
        return ""
    if number.startswith("+"):
        digits = re.sub(r"\D", "", number)
        if not 7 <= len(digits) <= 15:
            raise ValueError("invalid_phone")
        return f"+{digits}"
    if code not in COUNTRY_CODE_VALUES:
        raise ValueError("invalid_country_code")
    digits = re.sub(r"\D", "", number)
    full_digits = f"{code[1:]}{digits}"
    if not 7 <= len(full_digits) <= 15:
        raise ValueError("invalid_phone")
    if code == "+503" and len(digits) == 8:
        digits = f"{digits[:4]} {digits[4:]}"
    return f"{code} {digits}"


def split_international_phone(value, default_code="+503"):
    value = (value or "").strip()
    if not value:
        return default_code, ""
    compact = re.sub(r"[^\d+]", "", value)
    for code in sorted(COUNTRY_CODE_VALUES, key=len, reverse=True):
        if compact.startswith(code):
            return code, compact[len(code):]
    return default_code, value


def whatsapp_digits(value):
    return re.sub(r"\D", "", value or "")
