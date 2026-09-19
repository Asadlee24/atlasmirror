import sys

with open("/tmp/lez/flake.nix", "r") as f:
    content = f.read()

target = """          indexerFfiPackage = craneLib.buildPackage (
            commonArgs
            // {
              pname = "logos-execution-zone-indexer-ffi";
              version = "0.1.0";
              cargoExtraArgs = "-p indexer_ffi";
              postInstall = ''
                mkdir -p $out/include
                cp lez/indexer/ffi/indexer_ffi.h $out/include/
              ''
              + pkgs.lib.optionalString pkgs.stdenv.isDarwin ''
                install_name_tool -id @rpath/libindexer_ffi.dylib $out/lib/libindexer_ffi.dylib
              '';
            }
          );
        in
        {
          wallet = walletFfiPackage;
          indexer = indexerFfiPackage;
          default = walletFfiPackage;
        }"""

replacement = """          indexerFfiPackage = craneLib.buildPackage (
            commonArgs
            // {
              pname = "logos-execution-zone-indexer-ffi";
              version = "0.1.0";
              cargoExtraArgs = "-p indexer_ffi";
              postInstall = ''
                mkdir -p $out/include
                cp lez/indexer/ffi/indexer_ffi.h $out/include/
              ''
              + pkgs.lib.optionalString pkgs.stdenv.isDarwin ''
                install_name_tool -id @rpath/libindexer_ffi.dylib $out/lib/libindexer_ffi.dylib
              '';
            }
          );

          walletPackage = craneLib.buildPackage (
            commonArgs
            // {
              pname = "logos-execution-zone-wallet";
              version = "0.1.0";
              cargoExtraArgs = "-p wallet";
            }
          );

          sequencerPackage = craneLib.buildPackage (
            commonArgs
            // {
              pname = "logos-execution-zone-sequencer";
              version = "0.1.0";
              cargoExtraArgs = "-p sequencer_service";
            }
          );
        in
        {
          wallet = walletPackage;
          wallet-ffi = walletFfiPackage;
          sequencer = sequencerPackage;
          indexer = indexerFfiPackage;
          default = walletPackage;
        }"""

if target in content:
    with open("/tmp/lez/flake.nix", "w") as f:
        f.write(content.replace(target, replacement))
    print("SUCCESS: flake.nix updated with wallet and sequencer packages")
else:
    print("Target block not found, checking if already patched")
    if "walletPackage" in content:
        print("ALREADY PATCHED")
    else:
        print("FAILED to find target block")
        sys.exit(1)
