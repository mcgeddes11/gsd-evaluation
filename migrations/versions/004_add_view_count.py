from alembic import op
import sqlalchemy as sa

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('posts', sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    op.drop_column('posts', 'view_count')