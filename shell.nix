{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [ pkgs.chromium pkgs.python3 pkgs.poetry pkgs.wkhtmltopdf ];
}
