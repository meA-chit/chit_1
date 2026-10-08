-- A short code per subject, shown on the child's phone (kids/school). Filled in by the store for every subject without one: a subject keeps
-- its full name for lists and a code for tight places such as the week grid. The type (core, minor, elective) is shown beside it as c, m or e.
ALTER TABLE kid_subjects ADD COLUMN code TEXT;
