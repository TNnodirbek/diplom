from django.shortcuts import render


def home(request):
    return render(request, "website/home.html")


def about(request):
    return render(request, "website/about.html")


def services(request):
    return render(request, "website/services.html")


def doctors(request):
    doctors_list = []
    return render(request, "website/doctors.html", {"doctors": doctors_list})


def news(request):
    return render(request, "website/news.html")


def contact(request):
    return render(request, "website/contact.html")