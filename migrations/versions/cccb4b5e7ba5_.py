"""empty message

Revision ID: cccb4b5e7ba5
Revises: None
Create Date: 2016-09-07 14:34:54.359862

"""

# revision identifiers, used by Alembic.
revision = 'cccb4b5e7ba5'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('hydra_url',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('hydra_url', sa.String(length=255), server_default='', nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('role',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=50), nullable=False),
    sa.Column('password', sa.String(length=255), server_default='', nullable=False),
    sa.Column('reset_password_token', sa.String(length=100), server_default='', nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('confirmed_at', sa.DateTime(), nullable=True),
    sa.Column('is_active', sa.Boolean(), server_default='0', nullable=False),
    sa.Column('first_name', sa.String(length=100), server_default='', nullable=False),
    sa.Column('last_name', sa.String(length=100), server_default='', nullable=False),
    sa.Column('organization', sa.String(length=100), server_default='', nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    op.create_table('user_roles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_roles')
    op.drop_table('user')
    op.drop_table('role')
    op.drop_table('hydra_url')
    ### end Alembic commands ###