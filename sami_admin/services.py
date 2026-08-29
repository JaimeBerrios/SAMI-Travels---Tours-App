def generate_quotation_pdf(html, base_url):
    """Generate a PDF while keeping WeasyPrint lazy-loaded for HTML requests."""
    from weasyprint import HTML

    return HTML(string=html, base_url=base_url).write_pdf()
