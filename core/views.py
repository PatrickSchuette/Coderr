from django.http import HttpRequest, HttpResponse

ENDPOINT_GROUPS = {
    'Authentication': [
        ('POST /api/registration/', '/api/registration/'),
        ('POST /api/login/', '/api/login/'),
    ],
    'Profile': [
        ('GET/PATCH /api/profile/&lt;id&gt;/', None),
        ('GET /api/profiles/business/', '/api/profiles/business/'),
        ('GET /api/profiles/customer/', '/api/profiles/customer/'),
    ],
    'Offers': [
        ('GET/POST /api/offers/', '/api/offers/'),
        ('GET/PATCH/DELETE /api/offers/&lt;id&gt;/', None),
        ('GET /api/offerdetails/&lt;id&gt;/', None),
    ],
    'Orders': [
        ('GET/POST /api/orders/', '/api/orders/'),
        ('PATCH/DELETE /api/orders/&lt;id&gt;/', None),
        ('GET /api/order-count/&lt;business_user_id&gt;/', None),
        ('GET /api/completed-order-count/&lt;business_user_id&gt;/', None),
    ],
    'Reviews': [
        ('GET/POST /api/reviews/', '/api/reviews/'),
        ('PATCH/DELETE /api/reviews/&lt;id&gt;/', None),
    ],
    'Other': [
        ('GET /api/base-info/', '/api/base-info/'),
        ('Admin panel', '/admin/'),
    ],
}


def api_overview(request: HttpRequest) -> HttpResponse:
    """Render a simple clickable overview of all available API endpoints.

    This is a development convenience view, not part of the documented
    frontend contract - it only helps with manual orientation in the browser.
    Endpoints without a fixed path (they need an ID) are shown as plain text.
    """
    sections = ''
    for group_name, endpoints in ENDPOINT_GROUPS.items():
        items = ''
        for label, url in endpoints:
            if url:
                items += f'<li><a href="{url}">{label}</a></li>'
            else:
                items += f'<li>{label}</li>'
        sections += f'<h2>{group_name}</h2><ul>{items}</ul>'

    html = f'''
    <html>
        <head><title>Coderr API</title></head>
        <body style="font-family: sans-serif; max-width: 700px; margin: 40px auto;">
            <h1>Coderr API</h1>
            <p>Clickable links only work for GET endpoints without a required ID.</p>
            {sections}
        </body>
    </html>
    '''
    return HttpResponse(html)
