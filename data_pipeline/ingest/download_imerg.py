from pathlib import Path
import time

import earthaccess
import xarray as xr


# ==========================================
# 1. PATHS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

URL_LIST = (
    Path.home()
    / "Downloads"
    / "subset_GPM_3IMERGDF_07_20260830_225731_.txt"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "raw"
    / "imerg"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================
# 2. SETTINGS
# ==========================================

MAX_RETRIES = 3

MIN_FILE_SIZE = 5000


# ==========================================
# 3. LOGIN
# ==========================================

print("========================================")
print("IMERG DOWNLOAD")
print("========================================")

print("\nLogging into NASA Earthdata...")

earthaccess.login()

session = (
    earthaccess
    .get_requests_https_session()
)


# ==========================================
# 4. LOAD URL LIST
# ==========================================

if not URL_LIST.exists():

    raise FileNotFoundError(
        f"URL list not found:\n{URL_LIST}"
    )


urls = []

with open(
    URL_LIST,
    "r",
    encoding="utf-8"
) as file:

    for line in file:

        line = line.strip()

        if (
            "3B-DAY" in line
            and "HTTP_services.cgi" in line
        ):

            urls.append(line)


print(
    f"\nSubset URLs found: {len(urls)}"
)


if not urls:

    raise ValueError(
        "No IMERG subset URLs found."
    )


# ==========================================
# 5. DOWNLOAD LOOP
# ==========================================

total = len(urls)

downloaded = 0
skipped = 0
failed = 0


for index, url in enumerate(
    urls,
    start=1
):

    # --------------------------------------
    # Extract output filename
    # --------------------------------------

    filename = None

    if "LABEL=" in url:

        label = (
            url
            .split(
                "LABEL=",
                1
            )[1]
            .split(
                "&",
                1
            )[0]
        )

        filename = label


    if not filename:

        filename = (
            f"imerg_{index:04d}.nc4"
        )


    # LABEL is already a filename,
    # not a directory path.

    filename = Path(
        filename
    ).name


    output_file = (
        OUTPUT_DIR
        / filename
    )


    # --------------------------------------
    # Skip files that already exist
    # --------------------------------------

    if (
        output_file.exists()
        and
        output_file.stat().st_size > MIN_FILE_SIZE
    ):

        skipped += 1

        print(
            f"[{index}/{total}] "
            f"SKIP {filename}"
        )

        continue


    success = False


    # ======================================
    # RETRY LOOP
    # ======================================

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            print(
                f"\n[{index}/{total}] "
                f"Downloading {filename} "
                f"(attempt {attempt})"
            )


            response = session.get(
                url,
                timeout=180
            )

            response.raise_for_status()


            content = response.content


            # --------------------------------
            # Basic size check
            # --------------------------------

            if len(content) < MIN_FILE_SIZE:

                raise ValueError(
                    f"Response too small: "
                    f"{len(content)} bytes"
                )


            # --------------------------------
            # Validate as NetCDF4/HDF5
            # --------------------------------
            #
            # Do NOT rely on "CDF" magic bytes.
            # NetCDF4 uses HDF5 internally and
            # begins with the HDF5 signature.
            #

            temp_file = (
                OUTPUT_DIR
                / f".{filename}.tmp"
            )


            with open(
                temp_file,
                "wb"
            ) as file:

                file.write(content)


            try:

                with xr.open_dataset(
                    temp_file,
                    engine="netcdf4"
                ) as ds:

                    # Ensure expected variable exists

                    if (
                        "precipitation"
                        not in ds.variables
                    ):

                        raise ValueError(
                            "NetCDF does not contain "
                            "'precipitation'."
                        )

                    # Read metadata/data dimensions
                    # to force actual file validation.

                    _ = ds.dims

            finally:

                if temp_file.exists():

                    temp_file.unlink()


            # --------------------------------
            # Save final file
            # --------------------------------

            with open(
                output_file,
                "wb"
            ) as file:

                file.write(content)


            downloaded += 1

            print(
                f"SUCCESS: {filename} "
                f"({len(content):,} bytes)"
            )


            success = True

            break


        except Exception as e:

            print(
                f"ERROR: {e}"
            )


            if output_file.exists():

                output_file.unlink()


            if attempt < MAX_RETRIES:

                print(
                    "Retrying in 5 seconds..."
                )

                time.sleep(5)


    # ======================================
    # FAILURE
    # ======================================

    if not success:

        failed += 1

        print(
            f"FAILED: {filename}"
        )


# ==========================================
# 6. FINAL REPORT
# ==========================================

print("\n========================================")
print("IMERG DOWNLOAD COMPLETE")
print("========================================")

print(
    "Total URLs:",
    total
)

print(
    "Downloaded:",
    downloaded
)

print(
    "Skipped:",
    skipped
)

print(
    "Failed:",
    failed
)

print(
    "Output directory:",
    OUTPUT_DIR
)

print(
    "\nThe downloader is resumable."
)

print(
    "Valid existing files will be skipped."
)