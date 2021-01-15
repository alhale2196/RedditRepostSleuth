"""add filter_removed_matched to montiored sub

Revision ID: 7ecb5b67d5c9
Revises: 380abce0d196
Create Date: 2021-01-14 22:51:35.682060

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7ecb5b67d5c9'
down_revision = '380abce0d196'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('reddit_monitored_sub', sa.Column('filter_removed_matches', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('reddit_monitored_sub', 'filter_removed_matches')
    # ### end Alembic commands ###
