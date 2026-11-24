from sqlalchemy import (
    Integer, String, Boolean,
    create_engine,
    select, delete, update
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

##############################################################
# === CONFIG =================================================
##############################################################

DB_PATH = "sqlite:///baza.db"

engine = create_engine(DB_PATH)

class Base(DeclarativeBase):
    pass

##############################################################
# === MODELS =================================================
##############################################################

class Taomlar(Base):
    __tablename__ = "taomlar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    price: Mapped[int] = mapped_column(Integer)

class Foydalanuvchi(Base):
    __tablename__ = "foydalanuvchilar"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ism: Mapped[str] = mapped_column(String)
    telefon_raqam: Mapped[str] = mapped_column(String)
    rasm: Mapped[str] = mapped_column(String)
    telegram_id: Mapped[int] = mapped_column(Integer)
    username: Mapped[str] = mapped_column(String)
    is_admin: Mapped[bool] = mapped_column(Boolean)

from sqlalchemy import ForeignKey, UniqueConstraint


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, index=True)
    taom_id: Mapped[int] = mapped_column(ForeignKey("taomlar.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    __table_args__ = (
        UniqueConstraint("telegram_id", "taom_id"),
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer)

    full_name: Mapped[str] = mapped_column(String)
    phone: Mapped[str] = mapped_column(String)

    latitude: Mapped[float] = mapped_column()
    longitude: Mapped[float] = mapped_column()

    total_price: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String, default="pending")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))

    taom_name: Mapped[str] = mapped_column(String)
    price: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer)

##############################################################
# === CRUD ===================================================
##############################################################

# Taom

def add_taom(name, price):
    with Session(engine) as session:
        new_taom = Taomlar(
            name=name,
            price=price
        )
        session.add(new_taom)
        session.commit()
        print("taom qo`shildi")

def get_all_taomlar():
    with Session(engine) as session:
        taomlar = select(Taomlar)
        return session.execute(taomlar).scalars().all()

def taom_ochirish(id):
    with Session(engine) as session:
        taom = delete(Taomlar).where(Taomlar.id == id)
        session.execute(taom)
        session.commit()
        print("Taom o'chirildi")

# FOYDALANUVCHI

def add_foydalanuvchi(ism, telefon_raqam, rasm, telegram_id, username, is_admin):
    with Session(engine) as session:
        yangi_foy = Foydalanuvchi(
            ism=ism,
            telefon_raqam=telefon_raqam,
            rasm=rasm,
            telegram_id=telegram_id,
            username=username,
            is_admin=is_admin
        )
        session.add(yangi_foy)
        session.commit()

def get_one_user(telegram_id):
    with Session(engine) as session:
        foydalanuvchi = select(Foydalanuvchi).where(Foydalanuvchi.telegram_id == telegram_id)
        return session.execute(foydalanuvchi).scalar()

def change_admin_status(telegram_id, status):
    with Session(engine) as session:
        foy = update(Foydalanuvchi).where(Foydalanuvchi.telegram_id == telegram_id).values(is_admin=status)
        session.execute(foy)
        session.commit()

# change_admin_status(6150566915, True)

# BUYURTMALAR

from sqlalchemy import delete, update


def add_to_cart(telegram_id, taom_id):
    with Session(engine) as session:
        taom = session.get(Taomlar, taom_id)

        if not taom:
            return False

        item = session.scalar(
            select(CartItem).where(
                CartItem.telegram_id == telegram_id,
                CartItem.taom_id == taom_id
            )
        )

        if item:
            item.quantity += 1
        else:
            session.add(CartItem(
                telegram_id=telegram_id,
                taom_id=taom_id,
                quantity=1
            ))

        session.commit()
        return True


def get_cart(telegram_id):
    with Session(engine) as session:
        rows = session.execute(
            select(CartItem, Taomlar)
            .join(Taomlar, CartItem.taom_id == Taomlar.id)
            .where(CartItem.telegram_id == telegram_id)
        ).all()

        return [
            {
                "name": taom.name,
                "price": taom.price,
                "quantity": item.quantity
            }
            for item, taom in rows
        ]


def clear_cart(telegram_id):
    with Session(engine) as session:
        session.execute(
            delete(CartItem).where(
                CartItem.telegram_id == telegram_id
            )
        )
        session.commit()


def create_order(telegram_id, full_name, phone, latitude, longitude):
    with Session(engine) as session:
        rows = session.execute(
            select(CartItem, Taomlar)
            .join(Taomlar, CartItem.taom_id == Taomlar.id)
            .where(CartItem.telegram_id == telegram_id)
        ).all()

        if not rows:
            return None

        total = sum(
            item.quantity * taom.price
            for item, taom in rows
        )

        order = Order(
            telegram_id=telegram_id,
            full_name=full_name,
            phone=phone,
            latitude=latitude,
            longitude=longitude,
            total_price=total
        )

        session.add(order)
        session.flush()

        for item, taom in rows:
            session.add(OrderItem(
                order_id=order.id,
                taom_name=taom.name,
                price=taom.price,
                quantity=item.quantity
            ))

        session.execute(
            delete(CartItem).where(
                CartItem.telegram_id == telegram_id
            )
        )

        order_id = order.id
        session.commit()
        return order_id


def get_order(order_id):
    with Session(engine) as session:
        order = session.get(Order, order_id)

        if not order:
            return None

        items = session.scalars(
            select(OrderItem).where(
                OrderItem.order_id == order_id
            )
        ).all()

        return {
            "id": order.id,
            "telegram_id": order.telegram_id,
            "full_name": order.full_name,
            "phone": order.phone,
            "latitude": order.latitude,
            "longitude": order.longitude,
            "total_price": order.total_price,
            "status": order.status,
            "items": [
                {
                    "name": item.taom_name,
                    "price": item.price,
                    "quantity": item.quantity
                }
                for item in items
            ]
        }


def change_order_status(order_id, status):
    if status not in ("accepted", "cancelled"):
        return False

    with Session(engine) as session:
        result = session.execute(
            update(Order)
            .where(
                Order.id == order_id,
                Order.status == "pending"
            )
            .values(status=status)
        )

        session.commit()
        return result.rowcount == 1