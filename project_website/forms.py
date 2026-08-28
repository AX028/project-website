"""Validated, CSRF-protected contact form."""

from __future__ import annotations

import re

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class ContactForm(FlaskForm):  # type: ignore[misc]
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=80)])
    email = StringField("Email", validators=[DataRequired(), Length(max=254)])
    subject = StringField("Subject", validators=[DataRequired(), Length(min=3, max=120)])
    message = TextAreaField("Message", validators=[DataRequired(), Length(min=10, max=4000)])
    company = StringField("Company", validators=[Length(max=0)])

    def validate_email(self, field: StringField) -> None:
        if not EMAIL_PATTERN.fullmatch(field.data or ""):
            raise ValidationError("Enter a valid email address.")
