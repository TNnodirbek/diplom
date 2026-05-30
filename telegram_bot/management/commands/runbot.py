import os
from decimal import Decimal

from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand, CommandError

from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from accounts.models import Client
from animals.models import Animal
from requests_app.models import DangerReport, ServiceRequest


(
    MAIN_MENU,

    CLINIC_FULL_NAME,
    CLINIC_PHONE,
    CLINIC_ANIMAL_CHOICE,
    CLINIC_NEW_ANIMAL_TYPE,
    CLINIC_NEW_ANIMAL_NAME,

    VET_FULL_NAME,
    VET_PHONE,
    VET_ANIMAL_CHOICE,
    VET_NEW_ANIMAL_TYPE,
    VET_LOCATION,

    DANGER_TYPE,
    DANGER_LOCATION,
) = range(13)


BTN_CLINIC = "🏥 Klinikada davolash"
BTN_VET_CALL = "🚑 Veterinar chaqirish"
BTN_DANGER = "⚠️ Xavfli holatlar"

BTN_BACK = "◀️ Orqaga"
BTN_CANCEL = "❌ Bekor qilish"
BTN_SKIP = "⏭ O‘tkazib yuborish"
BTN_OTHER_ANIMAL = "➕ Boshqa hayvon"

BTN_SEND_PHONE = "📞 Telefon raqamni yuborish"
BTN_SEND_LOCATION = "📍 Joylashuvni yuborish"
BTN_WRITE_ADDRESS = "✍️ Manzilni yozib yuborish"
BTN_USE_OLD_LOCATION = "📌 Oldingi manzilni ishlatish"

SERVICE_CLINIC = "clinic"
SERVICE_VET_CALL = "vet_call"

CLINIC_PHONE_NUMBER = "+998 (70) 123-45-67"


def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        [
            [BTN_CLINIC],
            [BTN_VET_CALL],
            [BTN_DANGER],
        ],
        resize_keyboard=True,
    )


def phone_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(BTN_SEND_PHONE, request_contact=True)],
            [BTN_BACK, BTN_CANCEL],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def clinic_animal_type_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["It", "Mushuk"],
            ["Boshqa"],
            [BTN_BACK, BTN_CANCEL],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def vet_animal_type_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["Mol", "Ot"],
            ["Qo‘y", "Parrandalar"],
            ["It", "Mushuk"],
            ["Boshqa"],
            [BTN_BACK, BTN_CANCEL],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def animal_name_keyboard():
    return ReplyKeyboardMarkup(
        [
            [BTN_SKIP],
            [BTN_BACK, BTN_CANCEL],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def location_keyboard(has_old_location=False):
    buttons = [
        [KeyboardButton(BTN_SEND_LOCATION, request_location=True)],
    ]

    if has_old_location:
        buttons.append([BTN_USE_OLD_LOCATION])

    buttons.append([BTN_WRITE_ADDRESS])
    buttons.append([BTN_BACK, BTN_CANCEL])

    return ReplyKeyboardMarkup(
        buttons,
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def danger_type_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["O‘lik hayvon"],
            ["Quturgan/tajovuzkor hayvon gumoni"],
            ["Yuqumli kasallik gumoni"],
            ["Boshqa xavfli holat"],
            [BTN_BACK, BTN_CANCEL],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def existing_animals_keyboard(animals):
    buttons = []

    for animal in animals:
        animal_name = animal.name if animal.name else animal.get_animal_type_display()
        animal_code = animal.animal_code if animal.animal_code else "ID-YOQ"
        buttons.append([f"🐾 {animal_name} | {animal_code}"])

    buttons.append([BTN_OTHER_ANIMAL])
    buttons.append([BTN_BACK, BTN_CANCEL])

    return ReplyKeyboardMarkup(
        buttons,
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def animal_type_to_code(text):
    data = {
        "It": "dog",
        "Mushuk": "cat",
        "Mol": "cow",
        "Ot": "horse",
        "Qo‘y": "sheep",
        "Parrandalar": "bird",
        "Boshqa": "other",
    }
    return data.get(text, "other")


def danger_type_to_code(text):
    data = {
        "O‘lik hayvon": "dead_animal",
        "Quturgan/tajovuzkor hayvon gumoni": "aggressive_animal",
        "Yuqumli kasallik gumoni": "infectious_disease",
        "Boshqa xavfli holat": "other",
    }
    return data.get(text, "other")


@sync_to_async
def get_or_create_client(user):
    client, created = Client.objects.get_or_create(
        telegram_id=user.id,
        defaults={
            "telegram_username": user.username,
        },
    )

    changed = False

    if client.telegram_username != user.username:
        client.telegram_username = user.username
        changed = True

    if not client.client_code:
        client.save()
        changed = False

    if changed:
        client.save()

    return client


@sync_to_async
def update_client_name(client_id, full_name):
    client = Client.objects.get(id=client_id)
    client.full_name = full_name.strip()
    client.save()
    return client


@sync_to_async
def update_client_phone(client_id, phone):
    client = Client.objects.get(id=client_id)
    client.phone = phone.strip()
    client.save()
    return client


@sync_to_async
def update_client_address(client_id, address):
    client = Client.objects.get(id=client_id)
    client.address = address
    client.save()
    return client


@sync_to_async
def get_clinic_animals(client_id):
    animals = list(
        Animal.objects.filter(
            client_id=client_id,
            animal_type__in=["dog", "cat", "other"],
        ).order_by("-created_at")
    )

    for animal in animals:
        if not animal.animal_code:
            animal.save()

    return animals


@sync_to_async
def get_vet_animals(client_id):
    animals = list(
        Animal.objects.filter(client_id=client_id).order_by("-created_at")
    )

    for animal in animals:
        if not animal.animal_code:
            animal.save()

    return animals


@sync_to_async
def get_animal_by_code(client_id, animal_code):
    animal = Animal.objects.filter(
        client_id=client_id,
        animal_code=animal_code,
    ).first()

    return animal


@sync_to_async
def create_animal(client_id, animal_type, name=None):
    animal = Animal.objects.create(
        client_id=client_id,
        animal_type=animal_type,
        name=name if name else None,
    )

    if not animal.animal_code:
        animal.save()

    return animal


@sync_to_async
def get_last_vet_location(client_id):
    last_request = (
        ServiceRequest.objects
        .filter(client_id=client_id, service_type=SERVICE_VET_CALL)
        .exclude(address__isnull=True)
        .exclude(address="")
        .order_by("-created_at")
        .first()
    )

    if last_request:
        return {
            "address": last_request.address,
            "latitude": last_request.latitude,
            "longitude": last_request.longitude,
        }

    client = Client.objects.filter(id=client_id).first()

    if client and client.address:
        return {
            "address": client.address,
            "latitude": None,
            "longitude": None,
        }

    return None


@sync_to_async
def create_service_request(
    client_id,
    animal_id,
    service_type,
    address="",
    latitude=None,
    longitude=None,
):
    if service_type == SERVICE_CLINIC:
        problem_description = "Klinikada davolash uchun ariza"
        final_address = "Klinika ichida"
    else:
        problem_description = "Veterinar chaqirish uchun ariza"
        final_address = address if address else "Manzil kiritilmagan"

    request = ServiceRequest.objects.create(
        client_id=client_id,
        animal_id=animal_id,
        service_type=service_type,
        problem_description=problem_description,
        address=final_address,
        latitude=latitude,
        longitude=longitude,
        status="new",
    )

    client = Client.objects.get(id=client_id)
    animal = Animal.objects.get(id=animal_id)

    if service_type == SERVICE_VET_CALL and final_address != "Manzil kiritilmagan":
        client.address = final_address
        client.save()

    return {
        "request_id": request.id,
        "client_code": client.client_code,
        "animal_code": animal.animal_code,
    }


@sync_to_async
def create_danger_report(
    client_id,
    danger_type,
    address="",
    latitude=None,
    longitude=None,
):
    final_address = address if address else "Manzil kiritilmagan"

    report = DangerReport.objects.create(
        client_id=client_id,
        danger_type=danger_type,
        description="Telegram bot orqali xavfli holat yuborildi",
        address=final_address,
        latitude=latitude,
        longitude=longitude,
        status="new",
    )

    client = Client.objects.get(id=client_id)

    if final_address != "Manzil kiritilmagan":
        client.address = final_address
        client.save()

    return {
        "report_id": report.id,
        "client_code": client.client_code,
    }


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    user = update.effective_user
    client = await get_or_create_client(user)

    context.user_data["client_id"] = client.id

    if client.full_name:
        hello_text = f"Salom, {client.full_name}!"
    else:
        hello_text = "Assalomu alaykum!"

    await update.message.reply_text(
        f"{hello_text}\n"
        f"Ma’lumotlaringiz faqat veterinariya xizmati uchun ishlatiladi.\n\n"
        f"Xizmat turini tanlang:",
        reply_markup=main_menu_keyboard(),
    )

    return MAIN_MENU


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user

    client = await get_or_create_client(user)
    context.user_data["client_id"] = client.id

    if text == BTN_CLINIC:
        context.user_data["service_type"] = SERVICE_CLINIC

        if not client.full_name:
            await update.message.reply_text(
                "Ism-familiyangizni yozing:",
                reply_markup=ReplyKeyboardMarkup(
                    [[BTN_BACK, BTN_CANCEL]],
                    resize_keyboard=True,
                ),
            )
            return CLINIC_FULL_NAME

        if not client.phone:
            await update.message.reply_text(
                "Telefon raqamingizni yuboring:",
                reply_markup=phone_keyboard(),
            )
            return CLINIC_PHONE

        return await show_clinic_animals(update, context, client)

    if text == BTN_VET_CALL:
        context.user_data["service_type"] = SERVICE_VET_CALL

        if not client.full_name:
            await update.message.reply_text(
                "Ism-familiyangizni yozing:",
                reply_markup=ReplyKeyboardMarkup(
                    [[BTN_BACK, BTN_CANCEL]],
                    resize_keyboard=True,
                ),
            )
            return VET_FULL_NAME

        if not client.phone:
            await update.message.reply_text(
                "Telefon raqamingizni yuboring:",
                reply_markup=phone_keyboard(),
            )
            return VET_PHONE

        return await show_vet_animals(update, context, client)

    if text == BTN_DANGER:
        await update.message.reply_text(
            "Xavf turini tanlang:",
            reply_markup=danger_type_keyboard(),
        )
        return DANGER_TYPE

    await update.message.reply_text(
        "Iltimos, menyudan birini tanlang:",
        reply_markup=main_menu_keyboard(),
    )

    return MAIN_MENU


async def show_clinic_animals(update: Update, context: ContextTypes.DEFAULT_TYPE, client):
    animals = await get_clinic_animals(client.id)

    if animals:
        await update.message.reply_text(
            f"Salom, {client.full_name}.\n"
            f"Avvalgi hayvoningizni tanlang yoki boshqa hayvon qo‘shing:",
            reply_markup=existing_animals_keyboard(animals),
        )
        return CLINIC_ANIMAL_CHOICE

    await update.message.reply_text(
        "Hayvon turini tanlang:",
        reply_markup=clinic_animal_type_keyboard(),
    )

    return CLINIC_NEW_ANIMAL_TYPE


async def show_vet_animals(update: Update, context: ContextTypes.DEFAULT_TYPE, client):
    animals = await get_vet_animals(client.id)
    last_location = await get_last_vet_location(client.id)

    context.user_data["last_location"] = last_location

    location_text = ""

    if last_location:
        old_address = last_location.get("address") or "Oldingi manzil mavjud"
        location_text = f"\n\nOldingi manzil: {old_address}"

    if animals:
        await update.message.reply_text(
            f"Salom, {client.full_name}.\n"
            f"Veterinar chaqirish uchun hayvonni tanlang yoki boshqa hayvon qo‘shing:"
            f"{location_text}",
            reply_markup=existing_animals_keyboard(animals),
        )
        return VET_ANIMAL_CHOICE

    await update.message.reply_text(
        f"Hayvon turini tanlang:{location_text}",
        reply_markup=vet_animal_type_keyboard(),
    )

    return VET_NEW_ANIMAL_TYPE


async def ask_vet_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    last_location = context.user_data.get("last_location")
    has_old_location = bool(last_location)

    if has_old_location:
        old_address = last_location.get("address") or "Oldingi manzil mavjud"

        await update.message.reply_text(
            f"Joylashuvni tanlang.\n\n"
            f"Oldingi manzil: {old_address}",
            reply_markup=location_keyboard(True),
        )
    else:
        await update.message.reply_text(
            "Joylashuvni yuboring yoki manzilni yozing:",
            reply_markup=location_keyboard(False),
        )

    return VET_LOCATION


async def clinic_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == BTN_CANCEL:
        return await cancel(update, context)

    if text == BTN_BACK:
        return await go_main(update, context)

    client_id = context.user_data["client_id"]
    client = await update_client_name(client_id, text)

    if not client.phone:
        await update.message.reply_text(
            "Telefon raqamingizni yuboring:",
            reply_markup=phone_keyboard(),
        )
        return CLINIC_PHONE

    return await show_clinic_animals(update, context, client)


async def clinic_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text if update.message.text else ""

    if text == BTN_CANCEL:
        return await cancel(update, context)

    if text == BTN_BACK:
        await update.message.reply_text(
            "Ism-familiyangizni yozing:",
            reply_markup=ReplyKeyboardMarkup(
                [[BTN_BACK, BTN_CANCEL]],
                resize_keyboard=True,
            ),
        )
        return CLINIC_FULL_NAME

    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = text.strip()

    client_id = context.user_data["client_id"]
    client = await update_client_phone(client_id, phone)

    return await show_clinic_animals(update, context, client)


async def clinic_animal_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    client_id = context.user_data["client_id"]

    if text == BTN_CANCEL:
        return await cancel(update, context)

    if text == BTN_BACK:
        return await go_main(update, context)

    if text == BTN_OTHER_ANIMAL:
        await update.message.reply_text(
            "Hayvon turini tanlang:",
            reply_markup=clinic_animal_type_keyboard(),
        )
        return CLINIC_NEW_ANIMAL_TYPE

    if "|" in text:
        animal_code = text.split("|")[-1].strip()
        animal = await get_animal_by_code(client_id, animal_code)

        if animal:
            result = await create_service_request(
                client_id=client_id,
                animal_id=animal.id,
                service_type=SERVICE_CLINIC,
            )

            await update.message.reply_text(
                "✅ Arizangiz yuborildi.\n"
                f"Sizning klinika ID raqamingiz: {result['client_code']}\n"
                f"Hayvon ID raqami: {result['animal_code']}",
                reply_markup=main_menu_keyboard(),
            )
            return MAIN_MENU

    await update.message.reply_text(
        "Hayvon topilmadi. Qaytadan tanlang.",
        reply_markup=main_menu_keyboard(),
    )

    return MAIN_MENU


async def clinic_new_animal_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == BTN_CANCEL:
        return await cancel(update, context)

    if text == BTN_BACK:
        client = await get_or_create_client(update.effective_user)
        return await show_clinic_animals(update, context, client)

    context.user_data["animal_type"] = animal_type_to_code(text)

    await update.message.reply_text(
        "Hayvon ismini yozing.\n"
        "Kerak bo‘lmasa, o‘tkazib yuboring:",
        reply_markup=animal_name_keyboard(),
    )

    return CLINIC_NEW_ANIMAL_NAME


async def clinic_new_animal_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    client_id = context.user_data["client_id"]

    if text == BTN_CANCEL:
        return await cancel(update, context)

    if text == BTN_BACK:
        await update.message.reply_text(
            "Hayvon turini tanlang:",
            reply_markup=clinic_animal_type_keyboard(),
        )
        return CLINIC_NEW_ANIMAL_TYPE

    animal_name = None if text == BTN_SKIP else text.strip()

    animal = await create_animal(
        client_id=client_id,
        animal_type=context.user_data.get("animal_type", "other"),
        name=animal_name,
    )

    result = await create_service_request(
        client_id=client_id,
        animal_id=animal.id,
        service_type=SERVICE_CLINIC,
    )

    await update.message.reply_text(
        "✅ Arizangiz yuborildi.\n"
        f"Sizning klinika ID raqamingiz: {result['client_code']}\n"
        f"Hayvon ID raqami: {result['animal_code']}",
        reply_markup=main_menu_keyboard(),
    )

    return MAIN_MENU


async def vet_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == BTN_CANCEL:
        return await cancel(update, context)

    if text == BTN_BACK:
        return await go_main(update, context)

    client_id = context.user_data["client_id"]
    client = await update_client_name(client_id, text)

    if not client.phone:
        await update.message.reply_text(
            "Telefon raqamingizni yuboring:",
            reply_markup=phone_keyboard(),
        )
        return VET_PHONE

    return await show_vet_animals(update, context, client)


async def vet_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text if update.message.text else ""

    if text == BTN_CANCEL:
        return await cancel(update, context)

    if text == BTN_BACK:
        await update.message.reply_text(
            "Ism-familiyangizni yozing:",
            reply_markup=ReplyKeyboardMarkup(
                [[BTN_BACK, BTN_CANCEL]],
                resize_keyboard=True,
            ),
        )
        return VET_FULL_NAME

    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = text.strip()

    client_id = context.user_data["client_id"]
    client = await update_client_phone(client_id, phone)

    return await show_vet_animals(update, context, client)


async def vet_animal_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    client_id = context.user_data["client_id"]

    if text == BTN_CANCEL:
        return await cancel(update, context)

    if text == BTN_BACK:
        return await go_main(update, context)

    if text == BTN_OTHER_ANIMAL:
        await update.message.reply_text(
            "Hayvon turini tanlang:",
            reply_markup=vet_animal_type_keyboard(),
        )
        return VET_NEW_ANIMAL_TYPE

    if "|" in text:
        animal_code = text.split("|")[-1].strip()
        animal = await get_animal_by_code(client_id, animal_code)

        if animal:
            context.user_data["animal_id"] = animal.id
            return await ask_vet_location(update, context)

    await update.message.reply_text(
        "Hayvon topilmadi. Qaytadan tanlang.",
        reply_markup=main_menu_keyboard(),
    )

    return MAIN_MENU


async def vet_new_animal_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    client_id = context.user_data["client_id"]

    if text == BTN_CANCEL:
        return await cancel(update, context)

    if text == BTN_BACK:
        client = await get_or_create_client(update.effective_user)
        return await show_vet_animals(update, context, client)

    animal = await create_animal(
        client_id=client_id,
        animal_type=animal_type_to_code(text),
        name=None,
    )

    context.user_data["animal_id"] = animal.id

    return await ask_vet_location(update, context)


async def vet_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text if update.message.text else ""

    if text == BTN_CANCEL:
        return await cancel(update, context)

    if text == BTN_BACK:
        client = await get_or_create_client(update.effective_user)
        return await show_vet_animals(update, context, client)

    latitude = None
    longitude = None
    address = ""

    if text == BTN_USE_OLD_LOCATION:
        last_location = context.user_data.get("last_location")

        if not last_location:
            await update.message.reply_text(
                "Oldingi manzil topilmadi. Joylashuv yuboring yoki manzil yozing:",
                reply_markup=location_keyboard(False),
            )
            return VET_LOCATION

        address = last_location.get("address") or "Oldingi manzil"
        latitude = last_location.get("latitude")
        longitude = last_location.get("longitude")

    elif text == BTN_WRITE_ADDRESS:
        await update.message.reply_text(
            "Manzilni yozib yuboring:",
            reply_markup=ReplyKeyboardMarkup(
                [[BTN_BACK, BTN_CANCEL]],
                resize_keyboard=True,
            ),
        )
        return VET_LOCATION

    elif update.message.location:
        latitude = Decimal(str(update.message.location.latitude))
        longitude = Decimal(str(update.message.location.longitude))
        address = "Telegram orqali joylashuv yuborildi"

    else:
        address = text.strip()

        if not address:
            await update.message.reply_text(
                "Joylashuvni yuboring yoki manzilni yozing:",
                reply_markup=location_keyboard(
                    bool(context.user_data.get("last_location"))
                ),
            )
            return VET_LOCATION

    client_id = context.user_data["client_id"]
    animal_id = context.user_data.get("animal_id")

    if not animal_id:
        await update.message.reply_text(
            "Hayvon tanlanmadi. Qaytadan boshlang.",
            reply_markup=main_menu_keyboard(),
        )
        return MAIN_MENU

    result = await create_service_request(
        client_id=client_id,
        animal_id=animal_id,
        service_type=SERVICE_VET_CALL,
        address=address,
        latitude=latitude,
        longitude=longitude,
    )

    await update.message.reply_text(
        "✅ Veterinar chaqirish arizangiz yuborildi.\n"
        f"Sizning klinika ID raqamingiz: {result['client_code']}\n"
        f"Hayvon ID raqami: {result['animal_code']}\n\n"
        "Klinika administratori siz bilan bog‘lanadi.\n"
        f"☎️ Klinika: {CLINIC_PHONE_NUMBER}",
        reply_markup=main_menu_keyboard(),
    )

    return MAIN_MENU


async def danger_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == BTN_CANCEL:
        return await cancel(update, context)

    if text == BTN_BACK:
        return await go_main(update, context)

    context.user_data["danger_type"] = danger_type_to_code(text)

    await update.message.reply_text(
        "Xavfli holat joylashuvini yuboring yoki manzilni yozing:",
        reply_markup=location_keyboard(False),
    )

    return DANGER_LOCATION


async def danger_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text if update.message.text else ""

    if text == BTN_CANCEL:
        return await cancel(update, context)

    if text == BTN_BACK:
        await update.message.reply_text(
            "Xavf turini tanlang:",
            reply_markup=danger_type_keyboard(),
        )
        return DANGER_TYPE

    latitude = None
    longitude = None
    address = ""

    if text == BTN_WRITE_ADDRESS:
        await update.message.reply_text(
            "Xavfli holat manzilini yozib yuboring:",
            reply_markup=ReplyKeyboardMarkup(
                [[BTN_BACK, BTN_CANCEL]],
                resize_keyboard=True,
            ),
        )
        return DANGER_LOCATION

    if update.message.location:
        latitude = Decimal(str(update.message.location.latitude))
        longitude = Decimal(str(update.message.location.longitude))
        address = "Google Maps joylashuv yuborildi"
    else:
        address = text.strip()

        if not address:
            await update.message.reply_text(
                "Joylashuvni yuboring yoki manzilni yozing:",
                reply_markup=location_keyboard(False),
            )
            return DANGER_LOCATION

    client = await get_or_create_client(update.effective_user)

    result = await create_danger_report(
        client_id=client.id,
        danger_type=context.user_data.get("danger_type", "other"),
        address=address,
        latitude=latitude,
        longitude=longitude,
    )

    await update.message.reply_text(
        "✅ Xavfli holat xabari yuborildi.\n"
        "Status: Yangi xavfli holat\n"
        f"Sizning klinika ID raqamingiz: {result['client_code']}",
        reply_markup=main_menu_keyboard(),
    )

    return MAIN_MENU


async def go_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Asosiy menyu:",
        reply_markup=main_menu_keyboard(),
    )

    return MAIN_MENU


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "Amal bekor qilindi.",
        reply_markup=main_menu_keyboard(),
    )

    return MAIN_MENU


class Command(BaseCommand):
    help = "Telegram botni ishga tushirish"

    def handle(self, *args, **options):
        token = os.getenv("TELEGRAM_BOT_TOKEN")

        if not token:
            raise CommandError(
                "TELEGRAM_BOT_TOKEN topilmadi. Avval terminalga tokenni kiriting."
            )

        application = ApplicationBuilder().token(token).build()

        conversation_handler = ConversationHandler(
            entry_points=[
                CommandHandler("start", start),
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu),
            ],
            states={
                MAIN_MENU: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu),
                ],

                CLINIC_FULL_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, clinic_full_name),
                ],
                CLINIC_PHONE: [
                    MessageHandler(
                        filters.CONTACT | (filters.TEXT & ~filters.COMMAND),
                        clinic_phone,
                    ),
                ],
                CLINIC_ANIMAL_CHOICE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        clinic_animal_choice,
                    ),
                ],
                CLINIC_NEW_ANIMAL_TYPE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        clinic_new_animal_type,
                    ),
                ],
                CLINIC_NEW_ANIMAL_NAME: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        clinic_new_animal_name,
                    ),
                ],

                VET_FULL_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, vet_full_name),
                ],
                VET_PHONE: [
                    MessageHandler(
                        filters.CONTACT | (filters.TEXT & ~filters.COMMAND),
                        vet_phone,
                    ),
                ],
                VET_ANIMAL_CHOICE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        vet_animal_choice,
                    ),
                ],
                VET_NEW_ANIMAL_TYPE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        vet_new_animal_type,
                    ),
                ],
                VET_LOCATION: [
                    MessageHandler(
                        filters.LOCATION | (filters.TEXT & ~filters.COMMAND),
                        vet_location,
                    ),
                ],

                DANGER_TYPE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, danger_type),
                ],
                DANGER_LOCATION: [
                    MessageHandler(
                        filters.LOCATION | (filters.TEXT & ~filters.COMMAND),
                        danger_location,
                    ),
                ],
            },
            fallbacks=[
                CommandHandler("start", start),
                MessageHandler(filters.Regex(f"^{BTN_CANCEL}$"), cancel),
            ],
        )

        application.add_handler(conversation_handler)

        self.stdout.write(
            self.style.SUCCESS(
                "Telegram bot ishga tushdi. To‘xtatish uchun CTRL+C bosing."
            )
        )

        application.run_polling()