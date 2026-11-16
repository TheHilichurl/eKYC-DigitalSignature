"""
Pure Python 4-byte ZipAlign implementation for Android APKs.
Aligns uncompressed files (especially resources.arsc) to 4-byte boundaries.
"""

import zipfile
import io
import os
import sys

def zipalign(input_apk_path: str, output_apk_path: str, alignment: int = 4):
    with zipfile.ZipFile(input_apk_path, 'r') as in_zip:
        # We need to construct output zip manually to control local header padding
        out_buf = io.BytesIO()
        central_directory_entries = []
        
        for item in in_zip.infolist():
            data = in_zip.read(item.filename)
            local_offset = out_buf.tell()
            
            # Calculate current data offset without extra padding
            filename_bytes = item.filename.encode('utf-8')
            base_header_len = 30 + len(filename_bytes)
            
            # Calculate padding needed if uncompressed
            padding_len = 0
            if item.compress_type == zipfile.ZIP_STORED:
                data_offset = local_offset + base_header_len
                rem = data_offset % alignment
                if rem != 0:
                    padding_len = alignment - rem
            
            extra_bytes = b'\x00' * padding_len
            
            # Calculate DOS time
            dos_time = (item.date_time[0] - 1980) << 25 | item.date_time[1] << 21 | item.date_time[2] << 16 | \
                       item.date_time[3] << 11 | item.date_time[4] << 5 | (item.date_time[5] // 2)
            
            local_header = (
                b'PK\x03\x04' +
                (20).to_bytes(2, 'little') +
                item.flag_bits.to_bytes(2, 'little') +
                item.compress_type.to_bytes(2, 'little') +
                dos_time.to_bytes(4, 'little') +
                item.CRC.to_bytes(4, 'little') +
                item.compress_size.to_bytes(4, 'little') +
                item.file_size.to_bytes(4, 'little') +
                len(filename_bytes).to_bytes(2, 'little') +
                len(extra_bytes).to_bytes(2, 'little') +
                filename_bytes +
                extra_bytes
            )
            
            out_buf.write(local_header)
            
            # Verify data alignment
            actual_data_offset = out_buf.tell()
            if item.compress_type == zipfile.ZIP_STORED:
                assert actual_data_offset % alignment == 0, f"Unaligned entry {item.filename}"
                
            out_buf.write(data)
            
            # Save central directory info
            central_directory_entries.append((item, filename_bytes, extra_bytes, local_offset, dos_time))
            
        # Write Central Directory
        cd_start = out_buf.tell()
        for item, fn_bytes, ex_bytes, loc_offset, dos_time in central_directory_entries:
            cd_header = (
                b'PK\x01\x02' +
                (20).to_bytes(2, 'little') +       # version made by
                (20).to_bytes(2, 'little') +       # version needed
                item.flag_bits.to_bytes(2, 'little') +
                item.compress_type.to_bytes(2, 'little') +
                dos_time.to_bytes(4, 'little') +
                item.CRC.to_bytes(4, 'little') +
                item.compress_size.to_bytes(4, 'little') +
                item.file_size.to_bytes(4, 'little') +
                len(fn_bytes).to_bytes(2, 'little') +
                len(ex_bytes).to_bytes(2, 'little') +
                (0).to_bytes(2, 'little') +        # comment length
                (0).to_bytes(2, 'little') +        # disk number start
                (0).to_bytes(2, 'little') +        # internal file attributes
                (0).to_bytes(4, 'little') +        # external file attributes
                loc_offset.to_bytes(4, 'little') +
                fn_bytes +
                ex_bytes
            )
            out_buf.write(cd_header)
            
        cd_len = out_buf.tell() - cd_start
        
        # End of Central Directory
        eocd = (
            b'PK\x05\x06' +
            (0).to_bytes(2, 'little') +
            (0).to_bytes(2, 'little') +
            len(central_directory_entries).to_bytes(2, 'little') +
            len(central_directory_entries).to_bytes(2, 'little') +
            cd_len.to_bytes(4, 'little') +
            cd_start.to_bytes(4, 'little') +
            (0).to_bytes(2, 'little')
        )
        out_buf.write(eocd)
        
    with open(output_apk_path, 'wb') as f:
        f.write(out_buf.getvalue())
        
    print(f"[SUCCESS] ZipAlign completed: {output_apk_path}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python zipalign_apk.py in.apk out.apk")
        sys.exit(1)
    zipalign(sys.argv[1], sys.argv[2])
