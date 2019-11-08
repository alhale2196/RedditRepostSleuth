"""Add monitor checked table

Revision ID: f1a1e1d9c7fd
Revises: 3efb6c97a536
Create Date: 2019-11-02 12:43:43.516992

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1a1e1d9c7fd'
down_revision = '3efb6c97a536'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('reddit_monitored_sub_checked',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('post_id', sa.String(length=100), nullable=False),
    sa.Column('checked_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('reddit_monitored_sub_checked')
    # ### end Alembic commands ###