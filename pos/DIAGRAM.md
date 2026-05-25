// =============================
// POS Application Database Schema
// =============================

Table orders {
  id             int          [pk, increment]
  status         varchar(20)  [default: 'Pending', note: 'Pending | Completed | Cancelled']
  payment_method varchar(20)  [default: 'Cash', note: 'Cash | Card']
  customer_id    int          [ref: > customers.id, null] // Nullable for walk-ins
  created_at     timestamp    [default: `now()`]
  updated_at     timestamp    [default: `now()`]
}

Table products {
  id                int      [pk, increment]
  name              varchar(255)
  description       text
  price             decimal(10,2)
}

Table order_items {
  id                int      [pk, increment]
  order_id          int      [ref: > orders.id]       // FK to Order
  product_id        int      [ref: > products.id]     // FK to Product
  quantity          int      [default: 1]
  price_at_time_of_order decimal(10,2)
}

Table invoices {
  id                int      [pk, increment]
  order_id          int      [ref: > orders.id, unique] // One‑to‑One with Order
  invoice_number    varchar(50) [unique]
  is_split       boolean  [default: false]
  issued_at         timestamp [default: `now()`]
}

Table customers {
  id         int       [pk, increment]
  name       varchar(255)  [not null]
  email      varchar(255)  [unique]
  phone      varchar(50)
  address    text
  created_at timestamp [default: `now()`]
  updated_at timestamp [default: `now()`]
}

Table order_splits {
  id          int      [pk, increment]
  order_id    int      [ref: > orders.id, not null]
  customer_id int      [ref: > customers.id]   // the person responsible for this share
  amount      decimal(10,2) [not null]          // their part of the total
  note        varchar(255)                      // e.g. "pizza + soda"
}


Table payments {
  id            int      [pk, increment]
  invoice_id    int      [ref: > invoices.id, not null]
  customer_id   int      [ref: > customers.id]   // Nullable for walk‑ins
  amount        decimal(10,2) [not null]
  payment_method        varchar(20)
  reference     varchar(100)  // Gateway txn ID, card auth code, etc.
  paid_at       timestamp [default: `now()`]
}