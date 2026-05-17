# **alembic commands**

## initialization
> alembic init -t async some_directory

## revision
> alembic revision --autogenerate -m "some message"

## upgrade
> alembic upgrade head

## specific upgrade/downgrade
> alembic upgrade <revision>
>
> alembic downgrade <revision>

#### or (just one)
> alembic upgrade +1
>
> alembic downgrade -1

## monitoring
> alembic current
>
> alembic history
>
> alembic heads
