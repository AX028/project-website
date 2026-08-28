"""Public portfolio routes."""

from __future__ import annotations

import smtplib

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, url_for
from flask.typing import ResponseReturnValue

from .extensions import limiter
from .forms import ContactForm
from .mail import MailConfigurationError, send_contact

site = Blueprint("site", __name__)

CLASSES = (
    ("Barbarian", "Rage turns pressure into momentum."),
    ("Rogue", "Stealth and timing open critical windows."),
    ("Wizard", "Mana powers elemental attacks and shielding."),
    ("Ranger", "Marks and ranged volleys punish exposed targets."),
    ("Cleric", "Healing and cleansing sustain an encounter."),
    ("Paladin", "Sacred guards and smites control the front line."),
)
ENEMIES = (
    "Slime",
    "Goblin",
    "Skeleton",
    "Forest Sprout",
    "Wolf",
    "Bandit",
    "Orc Brute",
    "Cultist Mage",
    "Ogre",
    "Wraith",
    "Necromancer",
    "Ancient Dragon",
)


@site.get("/")
def index() -> str:
    snapshot = current_app.extensions["github_projects"].get_projects()
    return render_template(
        "index.html",
        form=ContactForm(),
        classes=CLASSES,
        enemies=ENEMIES,
        projects=snapshot.projects,
        cache_status=snapshot.cache,
    )


@site.post("/contact")
@limiter.limit("5 per minute; 20 per day")
def contact() -> ResponseReturnValue:
    form = ContactForm()
    if not form.validate_on_submit():
        flash("Please correct the highlighted fields and try again.", "error")
        snapshot = current_app.extensions["github_projects"].get_projects()
        return (
            render_template(
                "index.html",
                form=form,
                classes=CLASSES,
                enemies=ENEMIES,
                projects=snapshot.projects,
                cache_status=snapshot.cache,
            ),
            400,
        )
    try:
        send_contact(
            current_app.config,
            form.name.data,
            form.email.data,
            form.subject.data,
            form.message.data,
        )
    except (MailConfigurationError, OSError, smtplib.SMTPException):
        current_app.logger.warning("Contact delivery failed without retaining submission data")
        flash(
            "Delivery is temporarily unavailable. Please use the repository link instead.", "error"
        )
    else:
        flash("Message sent. Thanks for reaching out.", "success")
    return redirect(url_for("site.index") + "#contact", code=303)


@site.get("/healthz")
def health() -> tuple[dict[str, str], int]:
    return {"status": "ok"}, 200


@site.get("/api/projects")
def projects() -> ResponseReturnValue:
    snapshot = current_app.extensions["github_projects"].get_projects()
    return jsonify(
        {"projects": snapshot.projects, "cache": snapshot.cache, "fetched_at": snapshot.fetched_at}
    )
