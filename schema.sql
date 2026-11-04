-- =====================================================================
-- SYMPHONY OF SUMMITS — Production Database Schema
-- PostgreSQL 15+ (Supabase compatible)
-- Paste this entire file into Supabase SQL Editor → Run
-- =====================================================================

-- ---------- EXTENSIONS ----------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "citext";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ---------- ENUMS ----------
CREATE TYPE user_role AS ENUM ('customer', 'guide', 'admin', 'super_admin');
CREATE TYPE gender_type AS ENUM ('male', 'female', 'other', 'prefer_not_to_say');
CREATE TYPE id_proof_type AS ENUM ('aadhaar', 'passport', 'driving_license', 'voter_id', 'pan');

CREATE TYPE trek_category AS ENUM (
  'trek', 'expedition', 'pilgrimage', 'package', 'adventure', 'hillstation'
);
CREATE TYPE trek_scope AS ENUM ('indian', 'international');
CREATE TYPE difficulty_level AS ENUM ('easy', 'moderate', 'difficult', 'extreme');
CREATE TYPE season_type AS ENUM ('summer', 'monsoon', 'autumn', 'winter', 'all_year');

CREATE TYPE batch_status AS ENUM (
  'open', 'filling_fast', 'few_seats_left', 'sold_out', 'cancelled', 'completed'
);

CREATE TYPE booking_status AS ENUM (
  'pending', 'confirmed', 'cancelled', 'completed', 'refunded', 'no_show'
);
CREATE TYPE payment_status AS ENUM (
  'pending', 'processing', 'success', 'failed', 'refunded', 'partially_refunded'
);
CREATE TYPE payment_method AS ENUM (
  'upi_qr', 'payu', 'bank_transfer', 'cash'
);
CREATE TYPE refund_status AS ENUM ('requested', 'approved', 'rejected', 'processed');

CREATE TYPE gear_category AS ENUM (
  'backpack', 'footwear', 'clothing', 'sleeping', 'navigation',
  'safety', 'cooking', 'climbing', 'accessories'
);
CREATE TYPE rental_status AS ENUM (
  'reserved', 'picked_up', 'in_use', 'returned', 'overdue', 'damaged', 'cancelled'
);

CREATE TYPE lead_source AS ENUM (
  'website_form', 'quote_modal', 'whatsapp', 'phone', 'instagram',
  'facebook', 'google_ads', 'referral', 'walk_in', 'other'
);
CREATE TYPE lead_status AS ENUM (
  'new', 'contacted', 'qualified', 'quoted', 'converted', 'lost', 'spam'
);

CREATE TYPE notification_channel AS ENUM ('whatsapp', 'email', 'sms', 'push');
CREATE TYPE notification_status AS ENUM ('queued', 'sent', 'delivered', 'read', 'failed');

CREATE TYPE story_status AS ENUM ('draft', 'published', 'archived');


-- =====================================================================
-- 1. USERS
-- =====================================================================
CREATE TABLE users (
  id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  auth_id        UUID UNIQUE,
  email          CITEXT UNIQUE NOT NULL,
  phone          VARCHAR(20) UNIQUE,
  full_name      VARCHAR(120) NOT NULL,
  dob            DATE,
  gender         gender_type,
  nationality    VARCHAR(60) DEFAULT 'Indian',
  role           user_role NOT NULL DEFAULT 'customer',
  avatar_url     TEXT,
  address_line1  VARCHAR(200),
  address_line2  VARCHAR(200),
  city           VARCHAR(80),
  state          VARCHAR(80),
  country        VARCHAR(80) DEFAULT 'India',
  pincode        VARCHAR(12),
  emergency_contact_name   VARCHAR(120),
  emergency_contact_phone  VARCHAR(20),
  emergency_contact_rel    VARCHAR(40),
  email_verified_at  TIMESTAMPTZ,
  phone_verified_at  TIMESTAMPTZ,
  marketing_opt_in   BOOLEAN DEFAULT TRUE,
  whatsapp_opt_in    BOOLEAN DEFAULT TRUE,
  is_active          BOOLEAN DEFAULT TRUE,
  created_at         TIMESTAMPTZ DEFAULT NOW(),
  updated_at         TIMESTAMPTZ DEFAULT NOW(),
  deleted_at         TIMESTAMPTZ
);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_role  ON users(role) WHERE is_active = TRUE;

CREATE TABLE user_documents (
  id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  doc_type       id_proof_type NOT NULL,
  doc_number     VARCHAR(50),
  file_url       TEXT NOT NULL,
  verified       BOOLEAN DEFAULT FALSE,
  verified_by    UUID REFERENCES users(id),
  verified_at    TIMESTAMPTZ,
  expires_on     DATE,
  created_at     TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_user_docs_user ON user_documents(user_id);


-- =====================================================================
-- 2. CATALOG
-- =====================================================================
CREATE TABLE trips (
  id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  slug               VARCHAR(160) UNIQUE NOT NULL,
  title              VARCHAR(200) NOT NULL,
  subtitle           VARCHAR(300),
  category           trek_category NOT NULL,
  scope              trek_scope NOT NULL DEFAULT 'indian',
  difficulty         difficulty_level,
  region             VARCHAR(120),
  country            VARCHAR(80) DEFAULT 'India',
  state              VARCHAR(80),
  base_camp          VARCHAR(120),
  duration_days      SMALLINT NOT NULL CHECK (duration_days > 0),
  duration_nights    SMALLINT,
  max_altitude_m     INT,
  trek_distance_km   NUMERIC(6,2),
  best_season        season_type[],
  base_price         NUMERIC(10,2) NOT NULL CHECK (base_price >= 0),
  discount_pct       NUMERIC(5,2) DEFAULT 0 CHECK (discount_pct BETWEEN 0 AND 100),
  advance_amount     NUMERIC(10,2) DEFAULT 2000,
  gst_pct            NUMERIC(5,2) DEFAULT 5.00,
  currency           CHAR(3) DEFAULT 'INR',
  short_description  TEXT,
  overview_md        TEXT,
  itinerary          JSONB,
  inclusions         TEXT[],
  exclusions         TEXT[],
  things_to_carry    TEXT[],
  highlights         TEXT[],
  faqs               JSONB,
  cover_image        TEXT,
  gallery            TEXT[],
  trailer_video_url  TEXT,
  gpx_file_url       TEXT,
  brochure_pdf_url   TEXT,
  min_age            SMALLINT DEFAULT 10,
  max_age            SMALLINT DEFAULT 65,
  fitness_level      TEXT,
  medical_requirements TEXT,
  technical_grade    VARCHAR(20),
  seo_title          VARCHAR(200),
  seo_description    VARCHAR(300),
  seo_keywords       TEXT[],
  is_featured        BOOLEAN DEFAULT FALSE,
  is_published       BOOLEAN DEFAULT FALSE,
  published_at       TIMESTAMPTZ,
  created_by         UUID REFERENCES users(id),
  created_at         TIMESTAMPTZ DEFAULT NOW(),
  updated_at         TIMESTAMPTZ DEFAULT NOW(),
  deleted_at         TIMESTAMPTZ
);
CREATE INDEX idx_trips_slug        ON trips(slug);
CREATE INDEX idx_trips_category    ON trips(category) WHERE is_published = TRUE;
CREATE INDEX idx_trips_scope       ON trips(scope) WHERE is_published = TRUE;
CREATE INDEX idx_trips_difficulty  ON trips(difficulty) WHERE is_published = TRUE;
CREATE INDEX idx_trips_featured    ON trips(is_featured) WHERE is_published = TRUE;
CREATE INDEX idx_trips_title_trgm  ON trips USING gin (title gin_trgm_ops);

CREATE TABLE batches (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  trip_id         UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
  batch_code      VARCHAR(40) UNIQUE,
  start_date      DATE NOT NULL,
  end_date        DATE NOT NULL,
  total_seats     SMALLINT NOT NULL CHECK (total_seats > 0),
  booked_seats    SMALLINT NOT NULL DEFAULT 0 CHECK (booked_seats >= 0),
  reserved_seats  SMALLINT NOT NULL DEFAULT 0,
  price_override  NUMERIC(10,2),
  status          batch_status NOT NULL DEFAULT 'open',
  lead_guide_id   UUID REFERENCES users(id),
  pickup_point    VARCHAR(200),
  dropoff_point   VARCHAR(200),
  notes           TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT seats_not_overbooked CHECK (booked_seats + reserved_seats <= total_seats),
  CONSTRAINT valid_date_range     CHECK (end_date >= start_date)
);
CREATE INDEX idx_batches_trip        ON batches(trip_id);
CREATE INDEX idx_batches_start_date  ON batches(start_date) WHERE status != 'cancelled';
CREATE INDEX idx_batches_status      ON batches(status);


-- =====================================================================
-- 3. COUPONS (must exist before bookings - FK)
-- =====================================================================
CREATE TABLE coupons (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  code            VARCHAR(40) UNIQUE NOT NULL,
  description     TEXT,
  discount_type   VARCHAR(10) CHECK (discount_type IN ('flat', 'percent')),
  discount_value  NUMERIC(10,2) NOT NULL,
  max_discount    NUMERIC(10,2),
  min_order_value NUMERIC(10,2) DEFAULT 0,
  valid_from      TIMESTAMPTZ,
  valid_until     TIMESTAMPTZ,
  usage_limit     INT,
  per_user_limit  INT DEFAULT 1,
  used_count      INT DEFAULT 0,
  applicable_trip_ids  UUID[],
  applicable_categories trek_category[],
  is_active       BOOLEAN DEFAULT TRUE,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_coupons_code ON coupons(code) WHERE is_active = TRUE;


-- =====================================================================
-- 4. BOOKINGS
-- =====================================================================
CREATE TABLE bookings (
  id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  booking_code       VARCHAR(20) UNIQUE NOT NULL,
  user_id            UUID NOT NULL REFERENCES users(id),
  trip_id            UUID NOT NULL REFERENCES trips(id),
  batch_id           UUID NOT NULL REFERENCES batches(id),
  travellers_count   SMALLINT NOT NULL CHECK (travellers_count > 0),
  base_amount        NUMERIC(10,2) NOT NULL,
  discount_amount    NUMERIC(10,2) DEFAULT 0,
  gst_amount         NUMERIC(10,2) DEFAULT 0,
  total_amount       NUMERIC(10,2) NOT NULL,
  advance_paid       NUMERIC(10,2) DEFAULT 0,
  balance_due        NUMERIC(10,2) DEFAULT 0,
  status             booking_status NOT NULL DEFAULT 'pending',
  coupon_id          UUID REFERENCES coupons(id),
  special_requests   TEXT,
  pickup_point       VARCHAR(200),
  booked_from_ip     INET,
  booked_from_source lead_source,
  confirmed_at       TIMESTAMPTZ,
  cancelled_at       TIMESTAMPTZ,
  cancellation_reason TEXT,
  created_at         TIMESTAMPTZ DEFAULT NOW(),
  updated_at         TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_bookings_user     ON bookings(user_id);
CREATE INDEX idx_bookings_batch    ON bookings(batch_id);
CREATE INDEX idx_bookings_status   ON bookings(status);
CREATE INDEX idx_bookings_code     ON bookings(booking_code);
CREATE INDEX idx_bookings_created  ON bookings(created_at DESC);

CREATE TABLE travellers (
  id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  booking_id         UUID NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
  is_lead            BOOLEAN DEFAULT FALSE,
  full_name          VARCHAR(120) NOT NULL,
  age                SMALLINT CHECK (age BETWEEN 1 AND 120),
  gender             gender_type,
  nationality        VARCHAR(60),
  phone              VARCHAR(20),
  email              CITEXT,
  id_proof_type      id_proof_type,
  id_proof_number    VARCHAR(50),
  id_proof_url       TEXT,
  medical_conditions TEXT,
  blood_group        VARCHAR(5),
  dietary_needs      VARCHAR(100),
  tshirt_size        VARCHAR(10),
  emergency_contact_name  VARCHAR(120),
  emergency_contact_phone VARCHAR(20),
  insurance_policy_no VARCHAR(50),
  created_at         TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_travellers_booking ON travellers(booking_id);

CREATE TABLE payments (
  id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  booking_id              UUID NOT NULL REFERENCES bookings(id) ON DELETE RESTRICT,
  user_id                 UUID NOT NULL REFERENCES users(id),
  amount                  NUMERIC(10,2) NOT NULL CHECK (amount > 0),
  currency                CHAR(3) DEFAULT 'INR',
  method                  payment_method NOT NULL,
  status                  payment_status NOT NULL DEFAULT 'pending',
  is_advance              BOOLEAN DEFAULT FALSE,
  gateway                 VARCHAR(30),
  gateway_order_id        VARCHAR(80),
  gateway_payment_id      VARCHAR(80),
  gateway_signature       TEXT,
  gateway_response        JSONB,
  upi_vpa                 VARCHAR(80),
  upi_txn_ref             VARCHAR(60),
  upi_screenshot_url      TEXT,
  manually_verified_by    UUID REFERENCES users(id),
  manually_verified_at    TIMESTAMPTZ,
  invoice_number          VARCHAR(30) UNIQUE,
  invoice_url             TEXT,
  receipt_url             TEXT,
  failure_reason          TEXT,
  initiated_at            TIMESTAMPTZ DEFAULT NOW(),
  completed_at            TIMESTAMPTZ,
  created_at              TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_payments_booking      ON payments(booking_id);
CREATE INDEX idx_payments_status       ON payments(status);
CREATE INDEX idx_payments_gateway_oid  ON payments(gateway_order_id);
CREATE INDEX idx_payments_gateway_pid  ON payments(gateway_payment_id);

CREATE TABLE refunds (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  booking_id        UUID NOT NULL REFERENCES bookings(id),
  payment_id        UUID NOT NULL REFERENCES payments(id),
  amount            NUMERIC(10,2) NOT NULL CHECK (amount > 0),
  reason            TEXT,
  status            refund_status NOT NULL DEFAULT 'requested',
  requested_by      UUID REFERENCES users(id),
  approved_by       UUID REFERENCES users(id),
  gateway_refund_id VARCHAR(80),
  processed_at      TIMESTAMPTZ,
  created_at        TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_refunds_booking ON refunds(booking_id);


-- =====================================================================
-- 5. GEAR
-- =====================================================================
CREATE TABLE gear_items (
  id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  sku            VARCHAR(40) UNIQUE NOT NULL,
  name           VARCHAR(160) NOT NULL,
  category       gear_category NOT NULL,
  brand          VARCHAR(80),
  description    TEXT,
  size           VARCHAR(20),
  color          VARCHAR(40),
  daily_rent     NUMERIC(8,2) NOT NULL,
  weekly_rent    NUMERIC(8,2),
  deposit        NUMERIC(8,2) NOT NULL,
  total_stock    SMALLINT NOT NULL DEFAULT 0,
  available_stock SMALLINT NOT NULL DEFAULT 0,
  image_urls     TEXT[],
  is_active      BOOLEAN DEFAULT TRUE,
  created_at     TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT gear_stock_valid CHECK (available_stock <= total_stock AND available_stock >= 0)
);
CREATE INDEX idx_gear_category ON gear_items(category) WHERE is_active = TRUE;

CREATE TABLE gear_rentals (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  rental_code       VARCHAR(20) UNIQUE NOT NULL,
  user_id           UUID NOT NULL REFERENCES users(id),
  booking_id        UUID REFERENCES bookings(id),
  start_date        DATE NOT NULL,
  end_date          DATE NOT NULL,
  total_rent        NUMERIC(10,2) NOT NULL,
  total_deposit     NUMERIC(10,2) NOT NULL,
  status            rental_status NOT NULL DEFAULT 'reserved',
  pickup_notes      TEXT,
  return_notes      TEXT,
  damage_charges    NUMERIC(10,2) DEFAULT 0,
  created_at        TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT rental_dates_valid CHECK (end_date >= start_date)
);
CREATE INDEX idx_rentals_user ON gear_rentals(user_id);

CREATE TABLE gear_rental_items (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  rental_id       UUID NOT NULL REFERENCES gear_rentals(id) ON DELETE CASCADE,
  gear_item_id    UUID NOT NULL REFERENCES gear_items(id),
  quantity        SMALLINT NOT NULL DEFAULT 1,
  unit_rent       NUMERIC(8,2) NOT NULL,
  unit_deposit    NUMERIC(8,2) NOT NULL
);
CREATE INDEX idx_rental_items_rental ON gear_rental_items(rental_id);


-- =====================================================================
-- 6. LEADS & NOTIFICATIONS
-- =====================================================================
CREATE TABLE leads (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  full_name       VARCHAR(120) NOT NULL,
  email           CITEXT,
  phone           VARCHAR(20),
  city            VARCHAR(80),
  interested_trip_id UUID REFERENCES trips(id),
  travellers_count SMALLINT,
  preferred_date  DATE,
  budget          NUMERIC(10,2),
  message         TEXT,
  source          lead_source NOT NULL DEFAULT 'website_form',
  status          lead_status NOT NULL DEFAULT 'new',
  assigned_to     UUID REFERENCES users(id),
  utm_source      VARCHAR(80),
  utm_medium      VARCHAR(80),
  utm_campaign    VARCHAR(80),
  ip_address      INET,
  user_agent      TEXT,
  whatsapp_sent_at TIMESTAMPTZ,
  first_contacted_at TIMESTAMPTZ,
  converted_booking_id UUID REFERENCES bookings(id),
  notes           TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_leads_status  ON leads(status);
CREATE INDEX idx_leads_phone   ON leads(phone);
CREATE INDEX idx_leads_created ON leads(created_at DESC);

CREATE TABLE notifications (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id         UUID REFERENCES users(id),
  lead_id         UUID REFERENCES leads(id),
  booking_id      UUID REFERENCES bookings(id),
  channel         notification_channel NOT NULL,
  template_name   VARCHAR(80),
  recipient       VARCHAR(120) NOT NULL,
  subject         VARCHAR(200),
  body            TEXT,
  payload         JSONB,
  provider        VARCHAR(40),
  provider_message_id VARCHAR(120),
  status          notification_status DEFAULT 'queued',
  error           TEXT,
  sent_at         TIMESTAMPTZ,
  delivered_at    TIMESTAMPTZ,
  read_at         TIMESTAMPTZ,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_notif_user     ON notifications(user_id);
CREATE INDEX idx_notif_booking  ON notifications(booking_id);
CREATE INDEX idx_notif_status   ON notifications(status);
CREATE INDEX idx_notif_channel  ON notifications(channel);


-- =====================================================================
-- 7. STORIES, REVIEWS, INSTAGRAM
-- =====================================================================
CREATE TABLE stories (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  slug            VARCHAR(200) UNIQUE NOT NULL,
  title           VARCHAR(240) NOT NULL,
  subtitle        VARCHAR(300),
  cover_image     TEXT,
  body_md         TEXT NOT NULL,
  excerpt         VARCHAR(400),
  author_id       UUID REFERENCES users(id),
  trip_id         UUID REFERENCES trips(id),
  category        VARCHAR(60),
  tags            TEXT[],
  reading_minutes SMALLINT,
  status          story_status DEFAULT 'draft',
  featured        BOOLEAN DEFAULT FALSE,
  view_count      INT DEFAULT 0,
  seo_title       VARCHAR(200),
  seo_description VARCHAR(300),
  published_at    TIMESTAMPTZ,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_stories_status    ON stories(status);
CREATE INDEX idx_stories_published ON stories(published_at DESC) WHERE status = 'published';
CREATE INDEX idx_stories_tags      ON stories USING gin(tags);

CREATE TABLE reviews (
  id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id        UUID NOT NULL REFERENCES users(id),
  trip_id        UUID NOT NULL REFERENCES trips(id),
  booking_id     UUID REFERENCES bookings(id),
  rating         SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  title          VARCHAR(200),
  body           TEXT,
  images         TEXT[],
  is_verified    BOOLEAN DEFAULT FALSE,
  is_approved    BOOLEAN DEFAULT FALSE,
  helpful_count  INT DEFAULT 0,
  reply_from_admin TEXT,
  replied_at     TIMESTAMPTZ,
  created_at     TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (user_id, trip_id, booking_id)
);
CREATE INDEX idx_reviews_trip ON reviews(trip_id) WHERE is_approved = TRUE;

CREATE TABLE instagram_posts (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  ig_media_id     VARCHAR(60) UNIQUE NOT NULL,
  media_type      VARCHAR(20),
  media_url       TEXT NOT NULL,
  thumbnail_url   TEXT,
  permalink       TEXT,
  caption         TEXT,
  posted_at       TIMESTAMPTZ,
  fetched_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_ig_posted ON instagram_posts(posted_at DESC);


-- =====================================================================
-- 8. OPERATIONS
-- =====================================================================
CREATE TABLE pickup_points (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name        VARCHAR(120) NOT NULL,
  city        VARCHAR(80) NOT NULL,
  address     TEXT,
  latitude    NUMERIC(9,6),
  longitude   NUMERIC(9,6),
  is_active   BOOLEAN DEFAULT TRUE
);

CREATE TABLE newsletter_subscribers (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email       CITEXT UNIQUE NOT NULL,
  source      VARCHAR(60),
  confirmed   BOOLEAN DEFAULT FALSE,
  unsubscribed_at TIMESTAMPTZ,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE media_assets (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  owner_user_id UUID REFERENCES users(id),
  trip_id       UUID REFERENCES trips(id),
  story_id      UUID REFERENCES stories(id),
  storage_path  TEXT NOT NULL,
  cdn_url       TEXT,
  mime_type     VARCHAR(60),
  size_bytes    BIGINT,
  width         INT,
  height        INT,
  alt_text      VARCHAR(200),
  created_at    TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_media_trip  ON media_assets(trip_id);
CREATE INDEX idx_media_story ON media_assets(story_id);

CREATE TABLE audit_log (
  id          BIGSERIAL PRIMARY KEY,
  user_id     UUID REFERENCES users(id),
  action      VARCHAR(80) NOT NULL,
  entity      VARCHAR(60),
  entity_id   UUID,
  before_data JSONB,
  after_data  JSONB,
  ip_address  INET,
  user_agent  TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_audit_entity ON audit_log(entity, entity_id);
CREATE INDEX idx_audit_user   ON audit_log(user_id);
CREATE INDEX idx_audit_time   ON audit_log(created_at DESC);


-- =====================================================================
-- 9. TRIGGERS
-- =====================================================================
CREATE OR REPLACE FUNCTION touch_updated_at() RETURNS trigger AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_touch     BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
CREATE TRIGGER trg_trips_touch     BEFORE UPDATE ON trips
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
CREATE TRIGGER trg_batches_touch   BEFORE UPDATE ON batches
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
CREATE TRIGGER trg_bookings_touch  BEFORE UPDATE ON bookings
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
CREATE TRIGGER trg_stories_touch   BEFORE UPDATE ON stories
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
CREATE TRIGGER trg_leads_touch     BEFORE UPDATE ON leads
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

-- Booking code: SOS-YYYYMMDD-XXXXX
CREATE OR REPLACE FUNCTION gen_booking_code() RETURNS trigger AS $$
BEGIN
  IF NEW.booking_code IS NULL THEN
    NEW.booking_code := 'SOS-' || to_char(NOW(), 'YYYYMMDD') || '-' ||
                        upper(substr(md5(random()::text), 1, 5));
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER trg_booking_code BEFORE INSERT ON bookings
  FOR EACH ROW EXECUTE FUNCTION gen_booking_code();

-- Invoice number: INV-YYYYMM-XXXXX
CREATE SEQUENCE IF NOT EXISTS invoice_seq START 1001;
CREATE OR REPLACE FUNCTION gen_invoice_number() RETURNS trigger AS $$
BEGIN
  IF NEW.status = 'success' AND NEW.invoice_number IS NULL THEN
    NEW.invoice_number := 'INV-' || to_char(NOW(), 'YYYYMM') || '-' ||
                          lpad(nextval('invoice_seq')::text, 5, '0');
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER trg_invoice_number BEFORE UPDATE ON payments
  FOR EACH ROW EXECUTE FUNCTION gen_invoice_number();


-- =====================================================================
-- 10. SEAT INVENTORY FUNCTIONS (ACID-safe)
-- =====================================================================
CREATE OR REPLACE FUNCTION reserve_seats(
  p_batch_id UUID,
  p_seats    SMALLINT
) RETURNS BOOLEAN AS $$
DECLARE
  v_available SMALLINT;
BEGIN
  SELECT total_seats - booked_seats - reserved_seats
    INTO v_available
    FROM batches
   WHERE id = p_batch_id
   FOR UPDATE;

  IF v_available IS NULL THEN
    RAISE EXCEPTION 'Batch % not found', p_batch_id;
  END IF;

  IF v_available < p_seats THEN
    RETURN FALSE;
  END IF;

  UPDATE batches
     SET reserved_seats = reserved_seats + p_seats,
         status = CASE
           WHEN total_seats - booked_seats - reserved_seats - p_seats = 0 THEN 'sold_out'::batch_status
           WHEN total_seats - booked_seats - reserved_seats - p_seats <= 3 THEN 'few_seats_left'::batch_status
           WHEN total_seats - booked_seats - reserved_seats - p_seats <= total_seats * 0.3 THEN 'filling_fast'::batch_status
           ELSE status
         END
   WHERE id = p_batch_id;
  RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION confirm_seats(p_batch_id UUID, p_seats SMALLINT) RETURNS VOID AS $$
BEGIN
  UPDATE batches
     SET reserved_seats = GREATEST(reserved_seats - p_seats, 0),
         booked_seats   = booked_seats + p_seats
   WHERE id = p_batch_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION release_seats(p_batch_id UUID, p_seats SMALLINT) RETURNS VOID AS $$
BEGIN
  UPDATE batches
     SET reserved_seats = GREATEST(reserved_seats - p_seats, 0)
   WHERE id = p_batch_id;
END;
$$ LANGUAGE plpgsql;


-- =====================================================================
-- 11. ROW LEVEL SECURITY
-- =====================================================================
ALTER TABLE users         ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookings      ENABLE ROW LEVEL SECURITY;
ALTER TABLE travellers    ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments      ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE gear_rentals  ENABLE ROW LEVEL SECURITY;
ALTER TABLE reviews       ENABLE ROW LEVEL SECURITY;

CREATE POLICY users_self_select ON users
  FOR SELECT USING (auth.uid() = auth_id
    OR EXISTS (SELECT 1 FROM users u2 WHERE u2.auth_id = auth.uid() AND u2.role IN ('admin','super_admin')));

CREATE POLICY users_self_update ON users
  FOR UPDATE USING (auth.uid() = auth_id);

CREATE POLICY bookings_self ON bookings
  FOR SELECT USING (
    user_id = (SELECT id FROM users WHERE auth_id = auth.uid())
    OR EXISTS (SELECT 1 FROM users WHERE auth_id = auth.uid() AND role IN ('admin','super_admin'))
  );


-- =====================================================================
-- 12. VIEWS
-- =====================================================================
CREATE OR REPLACE VIEW upcoming_batches AS
SELECT b.id, b.batch_code, t.title, t.slug, t.category, t.difficulty,
       t.region, b.start_date, b.end_date, b.total_seats,
       (b.total_seats - b.booked_seats - b.reserved_seats) AS seats_available,
       COALESCE(b.price_override, t.base_price) AS price,
       b.status
  FROM batches b
  JOIN trips t ON t.id = b.trip_id
 WHERE b.start_date >= CURRENT_DATE
   AND b.status NOT IN ('cancelled','sold_out','completed')
   AND t.is_published = TRUE
 ORDER BY b.start_date;

CREATE OR REPLACE VIEW booking_summary AS
SELECT b.id, b.booking_code, b.status, b.total_amount, b.advance_paid,
       b.balance_due, u.full_name AS customer_name, u.email, u.phone,
       t.title AS trip_title, bt.start_date, bt.end_date,
       (SELECT COALESCE(SUM(amount),0) FROM payments
         WHERE booking_id = b.id AND status = 'success') AS total_paid,
       b.created_at
  FROM bookings b
  JOIN users u    ON u.id = b.user_id
  JOIN trips t    ON t.id = b.trip_id
  JOIN batches bt ON bt.id = b.batch_id;
