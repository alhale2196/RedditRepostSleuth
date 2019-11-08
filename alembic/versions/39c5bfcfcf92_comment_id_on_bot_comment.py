"""comment id on bot comment

Revision ID: 39c5bfcfcf92
Revises: 8aa2102f5bf5
Create Date: 2019-11-04 23:34:12.640984

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '39c5bfcfcf92'
down_revision = '8aa2102f5bf5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('reddit_bot_comment', sa.Column('comment_id', sa.String(length=20), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('reddit_bot_comment', 'comment_id')
    # ### end Alembic commands ###