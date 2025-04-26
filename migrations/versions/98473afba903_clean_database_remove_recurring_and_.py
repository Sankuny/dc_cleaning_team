"""🔥 Clean database: remove recurring and employee links

Revision ID: 98473afba903
Revises: 390158da4d85
Create Date: 2025-04-26 02:05:17.183757
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Identificadores de revisión
revision = '98473afba903'
down_revision = '390158da4d85'
branch_labels = None
depends_on = None

def upgrade():
    # 🔥 Primero eliminar la Foreign Key y la columna recurring_id
    with op.batch_alter_table('reservation', schema=None) as batch_op:
        batch_op.drop_constraint('reservation_recurring_id_fkey', type_='foreignkey')
        batch_op.drop_column('recurring_id')

    # 🔥 Luego sí eliminar la tabla recurring_service
    op.drop_table('recurring_service')


def downgrade():
    # 🔄 Restaurar columna recurring_id en reservation
    with op.batch_alter_table('reservation', schema=None) as batch_op:
        batch_op.add_column(sa.Column('recurring_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('reservation_recurring_id_fkey', 'recurring_service', ['recurring_id'], ['id'])

    # 🔄 Restaurar tabla recurring_service
    op.create_table(
        'recurring_service',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('service_type', sa.String(length=100), nullable=False),
        sa.Column('address', sa.String(length=200)),
        sa.Column('notes', sa.Text()),
        sa.Column('lat', sa.Float()),
        sa.Column('lng', sa.Float()),
        sa.Column('time', postgresql.TIME(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('frequency', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['usuario.id'], name='recurring_service_user_id_fkey')
    )
