from .models import SiteSettings
def site(request):
    fav_ids = []
    if request.user.is_authenticated:
        from apps.favorites.models import Favorite
        fav_ids = list(Favorite.objects.filter(user=request.user).values_list("car_id", flat=True))
    return {"site_settings": SiteSettings.load(), "fav_ids": fav_ids}
