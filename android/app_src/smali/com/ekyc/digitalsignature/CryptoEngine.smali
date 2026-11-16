.class public Lcom/ekyc/digitalsignature/CryptoEngine;
.super Ljava/lang/Object;
.source "CryptoEngine.java"

.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method

# Generates RSA-2048 KeyPair
.method public static generateRsaKeyPair()Ljava/security/KeyPair;
    .registers 2
    :try_start_0
    const-string v0, "RSA"
    invoke-static {v0}, Ljava/security/KeyPairGenerator;->getInstance(Ljava/lang/String;)Ljava/security/KeyPairGenerator;
    move-result-object v0
    const/16 v1, 0x800
    invoke-virtual {v0, v1}, Ljava/security/KeyPairGenerator;->initialize(I)V
    invoke-virtual {v0}, Ljava/security/KeyPairGenerator;->generateKeyPair()Ljava/security/KeyPair;
    move-result-object v0
    :try_end_e
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_e} :catch_f

    return-object v0

    :catch_f
    move-exception v0
    const/4 v0, 0x0
    return-object v0
.end method

# Signs data with SHA-256 and RSA PrivateKey
.method public static signSha256WithRsa([BLjava/security/PrivateKey;)[B
    .registers 3
    :try_start_0
    const-string v0, "SHA256withRSA"
    invoke-static {v0}, Ljava/security/Signature;->getInstance(Ljava/lang/String;)Ljava/security/Signature;
    move-result-object v0
    invoke-virtual {v0, p1}, Ljava/security/Signature;->initSign(Ljava/security/PrivateKey;)V
    invoke-virtual {v0, p0}, Ljava/security/Signature;->update([B)V
    invoke-virtual {v0}, Ljava/security/Signature;->sign()[B
    move-result-object v0
    :try_end_e
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_e} :catch_10

    return-object v0

    :catch_10
    move-exception v0
    const/4 v0, 0x0
    return-object v0
.end method

# Verifies SHA-256 with RSA PublicKey
.method public static verifySha256WithRsa([B[BLjava/security/PublicKey;)Z
    .registers 4
    :try_start_0
    const-string v0, "SHA256withRSA"
    invoke-static {v0}, Ljava/security/Signature;->getInstance(Ljava/lang/String;)Ljava/security/Signature;
    move-result-object v0
    invoke-virtual {v0, p2}, Ljava/security/Signature;->initVerify(Ljava/security/PublicKey;)V
    invoke-virtual {v0, p0}, Ljava/security/Signature;->update([B)V
    invoke-virtual {v0, p1}, Ljava/security/Signature;->verify([B)Z
    move-result v0
    :try_end_f
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_f} :catch_10

    return v0

    :catch_10
    move-exception v0
    const/4 v0, 0x0
    return v0
.end method

# Computes SHA-256 hash of bytes
.method public static computeSha256([B)[B
    .registers 2
    :try_start_0
    const-string v0, "SHA-256"
    invoke-static {v0}, Ljava/security/MessageDigest;->getInstance(Ljava/lang/String;)Ljava/security/MessageDigest;
    move-result-object v0
    invoke-virtual {v0, p0}, Ljava/security/MessageDigest;->digest([B)[B
    move-result-object v0
    :try_end_9
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_9} :catch_a

    return-object v0

    :catch_a
    move-exception v0
    const/4 v0, 0x0
    return-object v0
.end method

