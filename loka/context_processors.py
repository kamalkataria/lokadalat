from .models import Profile

def branch_details(request):
    if not request.user.is_authenticated:
        return {}

    if request.user.is_superuser:
        return {'branch_name': None, 'bankid': None}  # Avoid errors

    profile = Profile.objects.filter(user=request.user).first()
    if profile and profile.branch:
        return {
            'branch_name': profile.branch.branch_name,
            'bankid': profile.branch.regional_office.bank_id if profile.branch.regional_office else None,
        }
    return {}
