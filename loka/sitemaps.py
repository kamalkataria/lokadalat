from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = 'weekly'

    def items(self):
        return [
            'index',        # Home Page
            'setcalc',      # Settlement Calculation Page
        ]

    def location(self, item):
        return reverse(item)