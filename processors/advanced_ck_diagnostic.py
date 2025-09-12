#!/usr/bin/env python3
import os
import subprocess
import tempfile
import shutil
import time

def test_ck_with_different_configs(ck_path):
    """Testa CK com diferentes configurações"""
    print("\n=== Teste Avançado CK ===")
    
    tmpdir = tempfile.mkdtemp(prefix="ck_advanced_test_")
    try:
        # Cria estrutura de projeto mais realística
        src_main_java = os.path.join(tmpdir, "src", "main", "java", "com", "example")
        os.makedirs(src_main_java, exist_ok=True)
        
        # Arquivo Java mais complexo
        java_file = os.path.join(src_main_java, "TestClass.java")
        with open(java_file, 'w') as f:
            f.write("""
package com.example;

import java.util.List;
import java.util.ArrayList;

public class TestClass extends Object {
    private int field1;
    private String field2;
    private List<String> items = new ArrayList<>();
    
    public TestClass() {
        this.field1 = 0;
        this.field2 = "";
    }
    
    public void method1() {
        for (int i = 0; i < 10; i++) {
            if (i % 2 == 0) {
                System.out.println(i);
                items.add(String.valueOf(i));
            } else {
                try {
                    Thread.sleep(100);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }
        }
    }
    
    public int method2(int param) {
        try {
            return param * 2 + field1;
        } catch (Exception e) {
            return 0;
        }
    }
    
    public String getField2() {
        return field2;
    }
    
    public void setField2(String field2) {
        this.field2 = field2;
    }
}
""")
        
        # Segundo arquivo para ter múltiplas classes
        java_file2 = os.path.join(src_main_java, "AnotherClass.java")
        with open(java_file2, 'w') as f:
            f.write("""
package com.example;

public class AnotherClass {
    private TestClass testInstance;
    
    public void useTestClass() {
        testInstance = new TestClass();
        testInstance.method1();
        testInstance.setField2("test");
        String value = testInstance.getField2();
    }
}
""")
        
        print(f"Projeto de teste criado em: {tmpdir}")
        print(f"Estrutura:")
        for root, dirs, files in os.walk(tmpdir):
            level = root.replace(tmpdir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
        
        # Testa diferentes configurações
        configs = [
            ("Configuração 1: Básica", [tmpdir, "false", "0", "false"]),
            ("Configuração 2: Com JARs", [tmpdir, "true", "0", "false"]),
            ("Configuração 3: Com variáveis", [tmpdir, "false", "0", "true"]),
            ("Configuração 4: Só src/main/java", [os.path.join(tmpdir, "src", "main", "java"), "false", "0", "false"]),
            ("Configuração 5: Com limite de arquivos", [tmpdir, "false", "10", "false"]),
        ]
        
        for desc, params in configs:
            print(f"\n--- {desc} ---")
            
            output_dir = os.path.join(tmpdir, f"output_{len(params)}")
            os.makedirs(output_dir, exist_ok=True)
            
            cmd = ["java", "-jar", ck_path] + params + [output_dir]
            print("Comando:", " ".join(cmd))
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                print(f"Return code: {result.returncode}")
                if result.stdout.strip():
                    print(f"STDOUT: {result.stdout}")
                if result.stderr.strip():
                    print(f"STDERR: {result.stderr}")
                
                # Aguarda e verifica arquivos
                time.sleep(1)
                
                print("Arquivos gerados:")
                if os.path.exists(output_dir):
                    files = os.listdir(output_dir)
                    if files:
                        for file in files:
                            file_path = os.path.join(output_dir, file)
                            if os.path.isfile(file_path):
                                size = os.path.getsize(file_path)
                                print(f"  {file}: {size} bytes")
                                
                                # Mostra conteúdo se for CSV pequeno
                                if file.endswith('.csv') and size > 0 and size < 10000:
                                    print(f"    Primeiras linhas de {file}:")
                                    with open(file_path, 'r') as f:
                                        for i, line in enumerate(f):
                                            if i < 5:
                                                print(f"      {line.strip()}")
                    else:
                        print("  Nenhum arquivo gerado")
                else:
                    print(f"  Diretório {output_dir} não existe")
                    
            except subprocess.TimeoutExpired:
                print("  TIMEOUT: CK demorou mais de 60 segundos")
            except Exception as e:
                print(f"  ERRO: {e}")
    
    finally:
        print(f"\nLimpando diretório de teste: {tmpdir}")
        shutil.rmtree(tmpdir, ignore_errors=True)

def test_with_memory_options(ck_path):
    """Testa CK com diferentes opções de memória"""
    print("\n=== Teste com Opções de Memória ===")
    
    tmpdir = tempfile.mkdtemp(prefix="ck_memory_test_")
    try:
        # Projeto simples
        java_file = os.path.join(tmpdir, "Simple.java")
        with open(java_file, 'w') as f:
            f.write("""
public class Simple {
    public void method() {
        System.out.println("Hello");
    }
}
""")
        
        output_dir = os.path.join(tmpdir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        memory_options = [
            [],  # Sem opções especiais
            ["-Xmx2g"],  # 2GB heap
            ["-Xmx1g", "-XX:+UseG1GC"],  # 1GB com G1GC
            ["-Djava.awt.headless=true"],  # Headless
        ]
        
        for i, options in enumerate(memory_options):
            print(f"\n--- Teste {i+1}: {' '.join(options) if options else 'Padrão'} ---")
            
            cmd = ["java"] + options + ["-jar", ck_path, tmpdir, "false", "0", "false", output_dir]
            print("Comando:", " ".join(cmd))
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                print(f"Return code: {result.returncode}")
                print(f"STDOUT: {result.stdout}")
                if result.stderr.strip():
                    print(f"STDERR: {result.stderr}")
                
                files = os.listdir(output_dir) if os.path.exists(output_dir) else []
                print(f"Arquivos gerados: {files}")
                
                # Limpa para próximo teste
                if os.path.exists(output_dir):
                    shutil.rmtree(output_dir)
                    os.makedirs(output_dir)
                
            except subprocess.TimeoutExpired:
                print("  TIMEOUT")
            except Exception as e:
                print(f"  ERRO: {e}")
    
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

def check_jar_contents(ck_path):
    """Verifica o conteúdo do JAR"""
    print("\n=== Verificando Conteúdo do JAR ===")
    
    try:
        result = subprocess.run(["jar", "tf", ck_path], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            print(f"JAR contém {len(lines)} entradas")
            
            # Procura por classes principais
            main_classes = []
            for line in lines:
                if line.endswith('.class') and ('CK.class' in line or 'Runner.class' in line or 'Main.class' in line):
                    main_classes.append(line)
            
            print("Classes principais encontradas:")
            for cls in main_classes[:10]:  # Mostra até 10
                print(f"  {cls}")
                
            # Verifica manifest
            manifest_result = subprocess.run(["jar", "xf", ck_path, "META-INF/MANIFEST.MF"], 
                                           cwd=tempfile.gettempdir(), capture_output=True)
            if manifest_result.returncode == 0:
                manifest_file = os.path.join(tempfile.gettempdir(), "META-INF", "MANIFEST.MF")
                if os.path.exists(manifest_file):
                    print("\nMANIFEST.MF:")
                    with open(manifest_file, 'r') as f:
                        print(f.read())
        else:
            print("Não foi possível listar o conteúdo do JAR")
            print(result.stderr)
    except FileNotFoundError:
        print("Comando 'jar' não encontrado - instale o JDK")
    except Exception as e:
        print(f"Erro ao verificar JAR: {e}")

def main():
    import sys
    
    if len(sys.argv) != 2:
        print("Uso: python advanced_ck_diagnostic.py <caminho-para-ck.jar>")
        sys.exit(1)
    
    ck_path = sys.argv[1]
    
    print("Diagnóstico Avançado CK")
    print("=" * 60)
    
    check_jar_contents(ck_path)
    test_ck_with_different_configs(ck_path)
    test_with_memory_options(ck_path)
    
    print("\n" + "=" * 60)
    print("Diagnóstico avançado concluído")

if __name__ == "__main__":
    main()