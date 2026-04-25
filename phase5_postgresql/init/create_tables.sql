CREATE TABLE houses_core (
    house_id INT PRIMARY KEY,
    bldg_type VARCHAR(50),
    house_style VARCHAR(50),
    overall_qual INT,
    overall_cond INT,
    year_built INT,
    year_remod_add INT,
    gr_liv_area NUMERIC,
    bedroom_abvgr INT,
    kitchen_abvgr INT,
    kitchen_qual VARCHAR(50),
    full_bath INT,
    half_bath INT,
    fireplaces INT,
    central_air VARCHAR(10)
);

CREATE TABLE houses_location (
    house_id INT PRIMARY KEY,
    ms_zoning VARCHAR(50),
    lot_frontage NUMERIC,
    lot_area NUMERIC,
    neighborhood VARCHAR(100),
    CONSTRAINT fk_location_house
        FOREIGN KEY (house_id)
        REFERENCES houses_core(house_id)
        ON DELETE CASCADE
);

CREATE TABLE houses_structure (
    house_id INT PRIMARY KEY,
    total_bsmt_sf NUMERIC,
    first_flr_sf NUMERIC,
    second_flr_sf NUMERIC,
    garage_cars NUMERIC,
    garage_area NUMERIC,
    wood_deck_sf NUMERIC,
    open_porch_sf NUMERIC,
    screen_porch NUMERIC,
    pool_area NUMERIC,
    CONSTRAINT fk_structure_house
        FOREIGN KEY (house_id)
        REFERENCES houses_core(house_id)
        ON DELETE CASCADE
);

CREATE TABLE houses_sale (
    house_id INT PRIMARY KEY,
    mo_sold INT,
    yr_sold INT,
    sale_price NUMERIC,
    CONSTRAINT fk_sale_house
        FOREIGN KEY (house_id)
        REFERENCES houses_core(house_id)
        ON DELETE CASCADE
);

CREATE TABLE model_runs (
    run_id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    rmse_cv NUMERIC,
    mae_cv NUMERIC,
    r2_cv NUMERIC,
    rmse_test NUMERIC,
    mae_test NUMERIC,
    r2_test NUMERIC
);

CREATE TABLE predictions (
    prediction_id BIGSERIAL PRIMARY KEY,
    house_id INT NOT NULL,
    run_id INT NOT NULL,
    saleprice_real NUMERIC,
    saleprice_pred NUMERIC,
    abs_error NUMERIC,
    fold INT,
    CONSTRAINT fk_prediction_house
        FOREIGN KEY (house_id)
        REFERENCES houses_core(house_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_prediction_run
        FOREIGN KEY (run_id)
        REFERENCES model_runs(run_id)
        ON DELETE CASCADE
);