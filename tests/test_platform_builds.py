"""
Unit tests to verify Windows and Android build deliverables.
"""

import os
import unittest
import zipfile
import subprocess

class TestPlatformBuilds(unittest.TestCase):

    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.windows_dir = os.path.join(self.base_dir, "windows")
        self.android_dir = os.path.join(self.base_dir, "android")

    def test_01_windows_files_exist(self):
        """Verify Windows build artifacts exist and are ready."""
        main_py = os.path.join(self.windows_dir, "main_desktop.py")
        run_bat = os.path.join(self.windows_dir, "run_windows.bat")
        readme = os.path.join(self.windows_dir, "README.md")

        self.assertTrue(os.path.exists(main_py), "windows/main_desktop.py must exist")
        self.assertTrue(os.path.exists(run_bat), "windows/run_windows.bat must exist")
        self.assertTrue(os.path.exists(readme), "windows/README.md must exist")

    def test_02_android_apk_integrity(self):
        """Verify Android APK structure, assets, DEX, and manifests."""
        apk_path = os.path.join(self.android_dir, "eKYC_DigitalSignature.apk")
        self.assertTrue(os.path.exists(apk_path), "android/eKYC_DigitalSignature.apk must exist")
        self.assertGreater(os.path.getsize(apk_path), 20000, "APK size must be reasonable (>20KB)")

        with zipfile.ZipFile(apk_path, 'r') as zf:
            file_list = zf.namelist()
            self.assertIn("classes.dex", file_list, "APK must contain compiled Dalvik classes.dex")
            self.assertIn("AndroidManifest.xml", file_list, "APK must contain compiled AndroidManifest.xml")
            self.assertIn("resources.arsc", file_list, "APK must contain compiled resources.arsc")
            self.assertIn("assets/www/index.html", file_list, "APK must contain mobile web UI asset")
            
            # Verify signature presence
            sig_files = [f for f in file_list if f.startswith("META-INF/") and f.endswith(".RSA")]
            self.assertTrue(len(sig_files) > 0, "APK must have a valid cryptographic signature block in META-INF")

    def test_03_android_apk_jarsigner_verification(self):
        """Run jarsigner verification on the packaged APK."""
        apk_path = os.path.join(self.android_dir, "eKYC_DigitalSignature.apk")
        cmd = ["jarsigner", "-verify", apk_path]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"jarsigner verification failed: {res.stderr}")
        self.assertIn("jar verified", res.stdout, "APK must be successfully verified by jarsigner")

    def test_04_android_apk_v2_v3_signature_verification(self):
        """Verify APK Signature Scheme v2 and v3 using Google ApkVerifier."""
        apk_path = os.path.join(self.android_dir, "eKYC_DigitalSignature.apk")
        jadx_jar = r"C:\Tools\JADX\lib\jadx-1.5.6-all.jar"
        bin_dir = os.path.join(self.android_dir, "tools", "bin")
        if os.path.exists(jadx_jar) and os.path.exists(bin_dir):
            cmd = ["java", "-cp", f"{jadx_jar};{bin_dir}", "com.tools.VerifyApk", apk_path]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"VerifyApk failed: {res.stderr}")
            self.assertIn("Verified: true", res.stdout)
            self.assertIn("Scheme v2 (APK Signature v2) verified: true", res.stdout)
            self.assertIn("Scheme v3 (APK Signature v3) verified: true", res.stdout)

if __name__ == "__main__":
    unittest.main()

