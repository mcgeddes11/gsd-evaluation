from flask import Blueprint, render_template, jsonify, request, url_for, current_app, redirect, flash
from flask_login import login_required, current_user
from app import db, csrf
from app.models.media import Media
from app.blueprints.admin import admin_required