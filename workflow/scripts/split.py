import pysam
import os
import argparse

def process_bam(input_bam, cell_barcodes, out_prefix):
    # Open the input BAM file
    bamfile = pysam.AlignmentFile(input_bam, "rb")
    file_handles = {}

    new_rg_id = "RG1"
    new_rg_info = {
        'ID': new_rg_id,
        'SM': "Sample",
        'PL': 'ILLUMINA',
        'LB': 'Library',
        'PU': 'Unit'
    }

    for read in bamfile:
        # Process read if it has the "CB" tag (cell barcode)
        if read.has_tag("CB"):
            cb_tag = read.get_tag("CB")
            if cb_tag not in cell_barcodes:
                continue

            # Open a new output file for this barcode if not already open
            if cb_tag not in file_handles:
                header = bamfile.header.to_dict()

                # Replace RG field with a new one that uses this CB as the sample name
                rg_info = new_rg_info.copy()
                rg_info['SM'] = cb_tag
                header['RG'] = [rg_info]

                output_file = os.path.join(out_prefix, f"{cb_tag}.bam")
                file_handles[cb_tag] = pysam.AlignmentFile(output_file, "wb", header=header)
            
            # Write the read with new RG tag to the appropriate BAM file
            read.set_tag("RG", new_rg_id, value_type='Z')
            file_handles[cb_tag].write(read)

    # Close all opened output file handles
    for fh in file_handles.values():
        fh.close()

    # Close the input BAM file
    bamfile.close()

def read_cell_barcodes(input_file):
    barcodes = set()
    with open(input_file, 'r') as file:
        for line in file:
            barcode = line.strip()
            if barcode:
                barcodes.add(barcode)
    return barcodes

def main():
    input_bam = snakemake.input.bam
    cell_barcodes_txt = snakemake.input.cell_barcodes
    outdir = snakemake.output.outdir

    # Ensure the output directory exists
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    cell_barcodes = read_cell_barcodes(cell_barcodes_txt)
    process_bam(input_bam, cell_barcodes, outdir)

if __name__ == "__main__":
    main()

