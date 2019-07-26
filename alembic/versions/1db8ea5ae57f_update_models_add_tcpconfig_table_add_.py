"""update models add TcpConfig Table; add batch_no and addr_no to LuxSensor & IRSensor

Revision ID: 1db8ea5ae57f
Revises: f83f94b3ee11
Create Date: 2019-07-26 14:16:11.165134

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '1db8ea5ae57f'
down_revision = 'f83f94b3ee11'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tcp_config',
    sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ip', sa.String(length=50), nullable=True),
    sa.Column('port', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.alter_column('circuit_records', 'control',
               existing_type=mysql.TINYINT(display_width=1),
               type_=sa.BOOLEAN(),
               existing_nullable=True)
    op.alter_column('circuit_records', 'enable_netctr',
               existing_type=mysql.TINYINT(display_width=1),
               type_=sa.BOOLEAN(),
               existing_nullable=True)
    op.alter_column('circuit_records', 'oc',
               existing_type=mysql.TINYINT(display_width=1),
               type_=sa.BOOLEAN(),
               existing_nullable=True)
    op.alter_column('circuit_records', 'online',
               existing_type=mysql.TINYINT(display_width=1),
               type_=sa.BOOLEAN(),
               existing_nullable=True)
    op.alter_column('circuit_records', 'validity',
               existing_type=mysql.TINYINT(display_width=1),
               type_=sa.BOOLEAN(),
               existing_nullable=True)
    op.alter_column('circuit_records', 'visibility',
               existing_type=mysql.TINYINT(display_width=1),
               type_=sa.BOOLEAN(),
               existing_nullable=True)
    op.alter_column('elevator_status', 'direction',
               existing_type=mysql.SMALLINT(display_width=6),
               nullable=True)
    op.add_column('ir_sensor_status', sa.Column('status', sa.BOOLEAN(), nullable=True))
    op.add_column('ir_sensors', sa.Column('addr_no', sa.Integer(), nullable=True))
    op.add_column('ir_sensors', sa.Column('batch_no', sa.Integer(), nullable=True))
    op.add_column('ir_sensors', sa.Column('delay', sa.Integer(), nullable=True))
    op.add_column('ir_sensors', sa.Column('ip_config_id', sa.Integer(), nullable=True))
    op.add_column('ir_sensors', sa.Column('threshold', sa.Integer(), nullable=True))
    op.drop_index('ix_ir_sensors_device_index_code', table_name='ir_sensors')
    op.create_foreign_key(None, 'ir_sensors', 'tcp_config', ['ip_config_id'], ['id'], ondelete='SET NULL')
    op.drop_column('ir_sensors', 'device_index_code')
    op.add_column('lux_sensors', sa.Column('addr_no', sa.Integer(), nullable=True))
    op.add_column('lux_sensors', sa.Column('batch_no', sa.Integer(), nullable=True))
    op.add_column('lux_sensors', sa.Column('ip_config_id', sa.Integer(), nullable=True))
    op.drop_index('ix_lux_sensors_device_index_code', table_name='lux_sensors')
    op.create_foreign_key(None, 'lux_sensors', 'tcp_config', ['ip_config_id'], ['id'], ondelete='SET NULL')
    op.drop_column('lux_sensors', 'device_index_code')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('lux_sensors', sa.Column('device_index_code', mysql.VARCHAR(length=50), nullable=True))
    op.drop_constraint(None, 'lux_sensors', type_='foreignkey')
    op.create_index('ix_lux_sensors_device_index_code', 'lux_sensors', ['device_index_code'], unique=False)
    op.drop_column('lux_sensors', 'ip_config_id')
    op.drop_column('lux_sensors', 'batch_no')
    op.drop_column('lux_sensors', 'addr_no')
    op.add_column('ir_sensors', sa.Column('device_index_code', mysql.VARCHAR(length=50), nullable=True))
    op.drop_constraint(None, 'ir_sensors', type_='foreignkey')
    op.create_index('ix_ir_sensors_device_index_code', 'ir_sensors', ['device_index_code'], unique=False)
    op.drop_column('ir_sensors', 'threshold')
    op.drop_column('ir_sensors', 'ip_config_id')
    op.drop_column('ir_sensors', 'delay')
    op.drop_column('ir_sensors', 'batch_no')
    op.drop_column('ir_sensors', 'addr_no')
    op.drop_column('ir_sensor_status', 'status')
    op.alter_column('elevator_status', 'direction',
               existing_type=mysql.SMALLINT(display_width=6),
               nullable=False)
    op.alter_column('circuit_records', 'visibility',
               existing_type=sa.BOOLEAN(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    op.alter_column('circuit_records', 'validity',
               existing_type=sa.BOOLEAN(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    op.alter_column('circuit_records', 'online',
               existing_type=sa.BOOLEAN(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    op.alter_column('circuit_records', 'oc',
               existing_type=sa.BOOLEAN(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    op.alter_column('circuit_records', 'enable_netctr',
               existing_type=sa.BOOLEAN(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    op.alter_column('circuit_records', 'control',
               existing_type=sa.BOOLEAN(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    op.drop_table('tcp_config')
    # ### end Alembic commands ###
