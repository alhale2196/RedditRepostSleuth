"""remove response type from watch

Revision ID: 4db9740d5c18
Revises: 3c06d1d8e256
Create Date: 2019-12-03 21:12:46.540818

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '4db9740d5c18'
down_revision = '3c06d1d8e256'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('reddit_repost_watch', 'response_type')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('reddit_repost_watch', sa.Column('response_type', mysql.VARCHAR(length=100), nullable=False))
    # ### end Alembic commands ###