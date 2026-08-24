# Publishing checklist

Before publishing this repository to GitHub/HACS:

1. GitHub owner and `codeowners` are configured for `@dscomputers9404-coder`.
2. Create the repository as `ha-unifi-protect-events` under `dscomputers9404-coder`.
3. Ensure GitHub Issues are enabled.
4. Add a repository description and useful topics such as `home-assistant`, `hacs`, `unifi-protect`.
5. Add brand assets. Current HACS guidance requires brand assets for integration repositories; at minimum add a suitable `brand/icon.png` according to the current HACS/Home Assistant brand guidance.
6. Push the repository and verify that the HACS validation and Hassfest workflows pass.
7. Create a full GitHub Release for version `0.2.5` (not only a Git tag).
8. Test installation by adding the repository to HACS as a custom Integration repository.
9. Only after custom-repository testing, consider submitting it to the default HACS catalog.
