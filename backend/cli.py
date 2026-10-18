"""Explicit local/hosting operator commands, outside HTTP authentication."""
import click
from flask.cli import with_appcontext

from backend.extensions import db
from backend.models.member import Member
from backend.services.admin_recovery import AdminRecoveryService


@click.command('admin-recover')
@click.option('--member-id', required=True, type=click.IntRange(min=1))
@click.option('--apply', is_flag=True, help='Wiederherstellung nach interaktiver Bestätigung ausführen.')
@click.option('--reset-mfa', is_flag=True, help='Verlorenen zweiten Faktor samt Backup-Codes widerrufen.')
@with_appcontext
def admin_recover(member_id, apply, reset_mfa):
    """Vorhandenen aktiven Systemadmin über autorisierten Hostingzugang wiederherstellen."""
    member = db.session.get(Member, member_id)
    if not member or not member.is_active or not member.is_admin():
        db.session.rollback()
        raise click.ClickException('Ziel ist kein aktiver Systemadmin.')
    generation = member.auth_generation
    db.session.rollback()  # No transaction or lock while the operator enters secrets.
    click.echo(f'Ziel: aktiver Systemadmin ID {member_id}. Passwort und alte Zugänge werden ersetzt.')
    click.echo('MFA wird zurückgesetzt.' if reset_mfa else 'Bestehende MFA bleibt erhalten.')
    if not apply:
        click.echo('Vorschau: keine Änderungen. Ausführung verlangt --apply und Bestätigung.')
        return
    password = click.prompt('Neues Passwort', hide_input=True, confirmation_prompt=True)
    operator = click.prompt('Operatorreferenz (keine Geheimnisse)')
    reason = click.prompt('Grund / Vorgangsreferenz (keine Geheimnisse)')
    if click.prompt(f'Zur Bestätigung RECOVER {member_id} eingeben') != f'RECOVER {member_id}':
        raise click.ClickException('Abgebrochen; keine Änderungen.')
    try:
        AdminRecoveryService.recover(member_id, generation, password, operator, reason,
                                    reset_mfa=reset_mfa)
        db.session.commit()
    except ValueError as error:
        db.session.rollback()
        raise click.ClickException(str(error)) from None
    except Exception:
        db.session.rollback()
        raise click.ClickException('Wiederherstellung nicht bestätigt; Zustand und Audit prüfen.') from None
    click.echo('Wiederherstellung gespeichert. Neu anmelden und MFA sowie Backup-Codes prüfen.')
