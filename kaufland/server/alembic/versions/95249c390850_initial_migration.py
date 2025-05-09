"""Initial migration

Revision ID: 95249c390850
Revises: 
Create Date: 2025-03-09 18:54:53.511589

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '95249c390850'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('categories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_categories_id'), 'categories', ['id'], unique=False)
    op.create_table('manufacturers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_manufacturers_id'), 'manufacturers', ['id'], unique=False)
    op.create_table('products',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ean', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('manufacturer_id', sa.Integer(), nullable=True),
    sa.Column('category_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
    sa.ForeignKeyConstraint(['manufacturer_id'], ['manufacturers.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('ean')
    )
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)
    op.create_table('pictures',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('url', sa.String(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pictures_id'), 'pictures', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_pictures_id'), table_name='pictures')
    op.drop_table('pictures')
    op.drop_index(op.f('ix_products_id'), table_name='products')
    op.drop_table('products')
    op.drop_index(op.f('ix_manufacturers_id'), table_name='manufacturers')
    op.drop_table('manufacturers')
    op.drop_index(op.f('ix_categories_id'), table_name='categories')
    op.drop_table('categories')
    # ### end Alembic commands ###
