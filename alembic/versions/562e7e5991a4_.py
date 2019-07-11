"""empty message

Revision ID: 562e7e5991a4
Revises: 45360231ecf8
Create Date: 2019-07-11 16:48:09.768659

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '562e7e5991a4'
down_revision = '45360231ecf8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('circuit_alarms', sa.Column('alarm_or_type', sa.String(length=30), nullable=True))
    op.drop_column('circuit_alarms', 'alarm_type')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('circuit_alarms', sa.Column('alarm_type', mysql.VARCHAR(length=10), nullable=True))
    op.drop_column('circuit_alarms', 'alarm_or_type')
    # ### end Alembic commands ###
