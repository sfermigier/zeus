"""api_token

Revision ID: 8fbca7496953
Revises: 2d439d428034
Create Date: 2017-07-11 11:56:35.041186

"""
import zeus
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '8fbca7496953'
down_revision = '2d439d428034'
branch_labels = ()
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'api_token',
        sa.Column('id', zeus.db.types.guid.GUID(), nullable=False),
        sa.Column('access_token', sa.String(length=64), nullable=False),
        sa.Column('refresh_token', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('date_created', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('access_token'), sa.UniqueConstraint('refresh_token')
    )
    op.create_table(
        'api_token_repository_access',
        sa.Column('repository_id', zeus.db.types.guid.GUID(), nullable=False),
        sa.Column('api_token_id', zeus.db.types.guid.GUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ['api_token_id'],
            ['api_token.id'],
        ),
        sa.ForeignKeyConstraint(
            ['repository_id'],
            ['repository.id'],
        ), sa.PrimaryKeyConstraint('repository_id', 'api_token_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('api_token_repository_access')
    op.drop_table('api_token')
    # ### end Alembic commands ###