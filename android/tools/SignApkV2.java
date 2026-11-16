package com.tools;

import com.android.apksig.ApkSigner;
import java.io.File;
import java.io.FileInputStream;
import java.security.KeyStore;
import java.security.PrivateKey;
import java.security.cert.X509Certificate;
import java.util.ArrayList;
import java.util.List;

public class SignApkV2 {
    public static void main(String[] args) {
        try {
            if (args.length < 5) {
                System.err.println("Usage: java -cp ... com.tools.SignApkV2 input.apk output.apk keystore.jks password alias");
                System.exit(1);
            }
            File inputApk = new File(args[0]);
            File outputApk = new File(args[1]);
            File keystoreFile = new File(args[2]);
            String storePass = args[3];
            String keyAlias = args[4];

            System.out.println("[*] Loading Keystore from: " + keystoreFile.getAbsolutePath());
            KeyStore ks = KeyStore.getInstance(KeyStore.getDefaultType());
            try (FileInputStream fis = new FileInputStream(keystoreFile)) {
                ks.load(fis, storePass.toCharArray());
            }

            PrivateKey privateKey = (PrivateKey) ks.getKey(keyAlias, storePass.toCharArray());
            X509Certificate cert = (X509Certificate) ks.getCertificate(keyAlias);
            if (cert == null || privateKey == null) {
                System.err.println("[ERROR] Failed to load certificate or private key for alias: " + keyAlias);
                System.exit(1);
            }

            List<X509Certificate> certs = new ArrayList<>();
            certs.add(cert);

            ApkSigner.SignerConfig signerConfig = new ApkSigner.SignerConfig.Builder(
                keyAlias, privateKey, certs
            ).build();

            List<ApkSigner.SignerConfig> signerConfigs = new ArrayList<>();
            signerConfigs.add(signerConfig);

            System.out.println("[*] Signing APK with v1 (JAR), v2 (Full APK), and v3 (Key Rotation) schemes...");
            ApkSigner.Builder builder = new ApkSigner.Builder(signerConfigs)
                .setInputApk(inputApk)
                .setOutputApk(outputApk)
                .setV1SigningEnabled(true)
                .setV2SigningEnabled(true)
                .setV3SigningEnabled(true);

            ApkSigner signer = builder.build();
            signer.sign();
            System.out.println("[SUCCESS] APK signed successfully with Signature Schemes v1 + v2 + v3!");
        } catch (Exception e) {
            e.printStackTrace();
            System.exit(1);
        }
    }
}

