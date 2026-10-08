-- A short link code beside the QR secret, so an installed Home Screen app (separate storage on iOS) can pair by typing (ADR-0012).
ALTER TABLE kid_phone_pairings ADD COLUMN link_hash TEXT;
CREATE INDEX kid_phone_pairings_by_link ON kid_phone_pairings(link_hash);
