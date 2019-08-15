"""empty message

Revision ID: b92c21d051e0
Revises: 077e21e45317
Create Date: 2019-08-14 10:34:26.513320

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'b92c21d051e0'
down_revision = '077e21e45317'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('switches', sa.Column('tcp_config_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'switches', 'tcp_config', ['tcp_config_id'], ['id'], ondelete='set null')

