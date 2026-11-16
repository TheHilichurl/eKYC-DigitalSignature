package com.tools;

import com.android.apksig.ApkVerifier;
import java.io.File;

public class VerifyApk {
    public static void main(String[] args) {
        try {
            if (args.length < 1) {
                System.err.println("Usage: java ... com.tools.VerifyApk target.apk");
                System.exit(1);
            }
            File apkFile = new File(args[0]);
            ApkVerifier verifier = new ApkVerifier.Builder(apkFile).build();
            ApkVerifier.Result result = verifier.verify();

            System.out.println("=== APK SIGNATURE VERIFICATION REPORT ===");
            System.out.println("Verified: " + result.isVerified());
            System.out.println("Scheme v1 (JAR signing) verified: " + result.isVerifiedUsingV1Scheme());
            System.out.println("Scheme v2 (APK Signature v2) verified: " + result.isVerifiedUsingV2Scheme());
            System.out.println("Scheme v3 (APK Signature v3) verified: " + result.isVerifiedUsingV3Scheme());

            if (!result.isVerified()) {
                System.err.println("[ERROR] APK signature verification failed!");
                for (ApkVerifier.IssueWithParams issue : result.getErrors()) {
                    System.err.println(" - " + issue);
                }
                System.exit(1);
            }
        } catch (Exception e) {
            e.printStackTrace();
            System.exit(1);
        }
    }
}

