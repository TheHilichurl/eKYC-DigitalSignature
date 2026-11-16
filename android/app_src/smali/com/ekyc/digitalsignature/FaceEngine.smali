.class public Lcom/ekyc/digitalsignature/FaceEngine;
.super Ljava/lang/Object;
.source "FaceEngine.java"

.method public constructor <init>()V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method

# Native Android FaceDetector analysis of base64 image
.method public static detectFace(Ljava/lang/String;)Ljava/lang/String;
    .locals 14

    if-nez p0, :cond_not_null
    const-string v0, "{\"success\":false,\"faces_detected\":0}"
    return-object v0

    :cond_not_null
    :try_start_0
    # Strip data URI header if present
    const/16 v0, 0x2c
    invoke-virtual {p0, v0}, Ljava/lang/String;->indexOf(I)I
    move-result v0
    if-ltz v0, :cond_no_comma
    add-int/lit8 v0, v0, 0x1
    invoke-virtual {p0, v0}, Ljava/lang/String;->substring(I)Ljava/lang/String;
    move-result-object p0

    :cond_no_comma
    const/4 v0, 0x0
    invoke-static {p0, v0}, Landroid/util/Base64;->decode(Ljava/lang/String;I)[B
    move-result-object v1
    array-length v2, v1

    invoke-static {v1, v0, v2}, Landroid/graphics/BitmapFactory;->decodeByteArray([BII)Landroid/graphics/Bitmap;
    move-result-object v2

    if-nez v2, :cond_decoded
    const-string v0, "{\"success\":false,\"faces_detected\":0}"
    return-object v0

    :cond_decoded
    invoke-virtual {v2}, Landroid/graphics/Bitmap;->getWidth()I
    move-result v3
    invoke-virtual {v2}, Landroid/graphics/Bitmap;->getHeight()I
    move-result v4

    if-lez v3, :cond_invalid_size
    if-lez v4, :cond_invalid_size

    # Cap targetW at 240, ensure even width for FaceDetector
    const/16 v5, 0xf0
    if-gt v3, v5, :cond_calc_h
    move v5, v3

    :cond_calc_h
    const/4 v0, -0x2
    and-int/2addr v5, v0
    const/16 v0, 0x20
    if-lt v5, v0, :cond_invalid_size

    mul-int v6, v4, v5
    div-int/2addr v6, v3
    if-lt v6, v0, :cond_invalid_size

    # Convert to RGB_565 bitmap
    sget-object v7, Landroid/graphics/Bitmap$Config;->RGB_565:Landroid/graphics/Bitmap$Config;
    invoke-static {v5, v6, v7}, Landroid/graphics/Bitmap;->createBitmap(IILandroid/graphics/Bitmap$Config;)Landroid/graphics/Bitmap;
    move-result-object v7

    new-instance v8, Landroid/graphics/Canvas;
    invoke-direct {v8, v7}, Landroid/graphics/Canvas;-><init>(Landroid/graphics/Bitmap;)V

    new-instance v9, Landroid/graphics/Rect;
    const/4 v0, 0x0
    invoke-direct {v9, v0, v0, v3, v4}, Landroid/graphics/Rect;-><init>(IIII)V

    new-instance v10, Landroid/graphics/Rect;
    invoke-direct {v10, v0, v0, v5, v6}, Landroid/graphics/Rect;-><init>(IIII)V

    const/4 v11, 0x0
    invoke-virtual {v8, v2, v9, v10, v11}, Landroid/graphics/Canvas;->drawBitmap(Landroid/graphics/Bitmap;Landroid/graphics/Rect;Landroid/graphics/Rect;Landroid/graphics/Paint;)V
    invoke-virtual {v2}, Landroid/graphics/Bitmap;->recycle()V

    # Run android.media.FaceDetector
    new-instance v8, Landroid/media/FaceDetector;
    const/4 v9, 0x1
    invoke-direct {v8, v5, v6, v9}, Landroid/media/FaceDetector;-><init>(III)V

    new-array v9, v9, [Landroid/media/FaceDetector$Face;
    invoke-virtual {v8, v7, v9}, Landroid/media/FaceDetector;->findFaces(Landroid/graphics/Bitmap;[Landroid/media/FaceDetector$Face;)I
    move-result v10
    invoke-virtual {v7}, Landroid/graphics/Bitmap;->recycle()V

    if-lez v10, :cond_no_face
    const/4 v0, 0x0
    aget-object v11, v9, v0
    if-eqz v11, :cond_no_face

    # Confidence >= 0.35f
    invoke-virtual {v11}, Landroid/media/FaceDetector$Face;->confidence()F
    move-result v12
    const v0, 0x3eb33333
    cmpg-float v0, v12, v0
    if-ltz v0, :cond_no_face

    # eyesDistance >= 10.0f
    invoke-virtual {v11}, Landroid/media/FaceDetector$Face;->eyesDistance()F
    move-result v13
    const/high16 v0, 0x41200000
    cmpg-float v0, v13, v0
    if-ltz v0, :cond_no_face

    new-instance v0, Landroid/graphics/PointF;
    invoke-direct {v0}, Landroid/graphics/PointF;-><init>()V
    invoke-virtual {v11, v0}, Landroid/media/FaceDetector$Face;->getMidPoint(Landroid/graphics/PointF;)V

    iget v1, v0, Landroid/graphics/PointF;->x:F
    iget v2, v0, Landroid/graphics/PointF;->y:F

    const v3, 0x3f933333
    mul-float v3, v13, v3
    sub-float v4, v1, v3

    const/high16 v7, 0x3f400000
    mul-float v7, v13, v7
    sub-float v8, v2, v7

    const v9, 0x40133333
    mul-float v9, v13, v9

    const/high16 v10, 0x40300000
    mul-float v10, v13, v10

    new-instance v11, Ljava/lang/StringBuilder;
    invoke-direct {v11}, Ljava/lang/StringBuilder;-><init>()V

    const-string v0, "{\"success\":true,\"faces_detected\":1,\"confidence\":"
    invoke-virtual {v11, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v11, v12}, Ljava/lang/StringBuilder;->append(F)Ljava/lang/StringBuilder;

    const-string v0, ",\"bbox\":["
    invoke-virtual {v11, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    float-to-int v0, v4
    invoke-virtual {v11, v0}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    const-string v0, ","
    invoke-virtual {v11, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    float-to-int v0, v8
    invoke-virtual {v11, v0}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    const-string v0, ","
    invoke-virtual {v11, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    float-to-int v0, v9
    invoke-virtual {v11, v0}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    const-string v0, ","
    invoke-virtual {v11, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    float-to-int v0, v10
    invoke-virtual {v11, v0}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    const-string v0, "],\"image_width\":"
    invoke-virtual {v11, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v11, v5}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    const-string v0, ",\"image_height\":"
    invoke-virtual {v11, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v11, v6}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    const-string v0, "}"
    invoke-virtual {v11, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v11}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0

    :cond_no_face
    new-instance v11, Ljava/lang/StringBuilder;
    invoke-direct {v11}, Ljava/lang/StringBuilder;-><init>()V
    const-string v0, "{\"success\":true,\"faces_detected\":0,\"image_width\":"
    invoke-virtual {v11, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v11, v5}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    const-string v0, ",\"image_height\":"
    invoke-virtual {v11, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v11, v6}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    const-string v0, "}"
    invoke-virtual {v11, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v11}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0

    :cond_invalid_size
    invoke-virtual {v2}, Landroid/graphics/Bitmap;->recycle()V
    const-string v0, "{\"success\":false,\"faces_detected\":0}"
    return-object v0
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    :catch_0
    move-exception v0
    const-string v0, "{\"success\":false,\"faces_detected\":0}"
    return-object v0
.end method

