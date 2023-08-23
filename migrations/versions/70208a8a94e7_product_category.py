"""product_category

Revision ID: 70208a8a94e7
Revises: 56f8e106faaa
Create Date: 2023-08-23 19:53:13.939949

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '70208a8a94e7'
down_revision = '56f8e106faaa'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Category', sa.Column('name', sa.String(), nullable=False))
    op.drop_constraint('Category_category_name_key', 'Category', type_='unique')
    op.create_unique_constraint(None, 'Category', ['name'])
    op.drop_column('Category', 'category_name')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Category', sa.Column('category_name', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'Category', type_='unique')
    op.create_unique_constraint('Category_category_name_key', 'Category', ['category_name'])
    op.drop_column('Category', 'name')
    # ### end Alembic commands ###