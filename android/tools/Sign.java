import com.android.apksig.ApkSigner;
import java.io.File;
import java.io.FileInputStream;
import java.security.KeyStore;
import java.security.PrivateKey;
import java.security.cert.X509Certificate;
import java.util.Collections;

/**
 * Aligns and signs an APK (v1 + v2 + v3 signature schemes) using the apksig
 * library that ships inside bundletool-all.jar.
 *
 * java -cp bundletool-all.jar:. Sign <keystore> <alias> <storepass> <in.apk> <out.apk>
 */
public class Sign {
    public static void main(String[] a) throws Exception {
        KeyStore ks = KeyStore.getInstance(new File(a[0]), a[2].toCharArray());
        PrivateKey key = (PrivateKey) ks.getKey(a[1], a[2].toCharArray());
        X509Certificate cert = (X509Certificate) ks.getCertificate(a[1]);
        ApkSigner.SignerConfig sc = new ApkSigner.SignerConfig.Builder(
                "UPLOAD", key, Collections.singletonList(cert)).build();
        new ApkSigner.Builder(Collections.singletonList(sc))
                .setInputApk(new File(a[3]))
                .setOutputApk(new File(a[4]))
                .setMinSdkVersion(24)
                .setV1SigningEnabled(true)
                .setV2SigningEnabled(true)
                .setV3SigningEnabled(true)
                .build()
                .sign();
        System.out.println("signed " + a[4]);
    }
}
