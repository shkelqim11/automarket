from django.contrib import admin
from .models import Brand, Car, CarImage, ListingView, VipListing

class ImageInline(admin.TabularInline):
    model = CarImage; extra = 0

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    search_fields = ["name"]; prepopulated_fields = {"slug": ("name",)}

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ["title", "brand", "price", "city", "status", "is_vip", "owner", "created_at"]
    list_filter = ["status", "is_vip", "brand", "fuel", "city"]
    search_fields = ["title", "model", "owner__username", "phone"]
    list_editable = ["status", "is_vip"]
    inlines = [ImageInline]
    actions = ["approve", "reject", "make_vip", "remove_vip"]
    @admin.action(description="Approve selected")
    def approve(self, request, qs): qs.update(status=Car.Status.PUBLISHED)
    @admin.action(description="Reject selected")
    def reject(self, request, qs): qs.update(status=Car.Status.REJECTED)
    @admin.action(description="Activate VIP")
    def make_vip(self, request, qs): qs.update(is_vip=True)
    @admin.action(description="Deactivate VIP")
    def remove_vip(self, request, qs): qs.update(is_vip=False)

admin.site.register(ListingView)
admin.site.register(VipListing)
