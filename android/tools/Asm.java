import java.io.File;
public class Asm { public static void main(String[] a) throws Exception {
  brut.androlib.src.SmaliBuilder.build(new brut.directory.ExtFile(new File(a[0])), new File(a[1]), Integer.parseInt(a[2]));
  System.out.println("assembled " + a[1]); } }
