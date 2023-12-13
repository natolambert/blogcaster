from pydub import AudioSegment
import argparse

if __name__ == "__main__":
    # import argparse and define txt file path and output path
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, help="input audio file")
    parser.add_argument("--output", type=str, default="final_audio.mp3", help="output mp3 file path")
    parser.add_argument("--fade_time", type=int, default=3000, help="cross fade time in ms")
    args = parser.parse_args()
    
    # load hardcoded intro and outro music 
    intro = AudioSegment.from_wav("audio/intro-v2.wav")
    outro = AudioSegment.from_wav("audio/outro-fade.wav")
    farewell = AudioSegment.from_mp3("audio/farewell.mp3")
    outro = AudioSegment.silent(1500) + farewell + outro
    generation = AudioSegment.from_mp3(args.input)
    
    # add silence to beginning and end of generation equal to 3/4 of fade time
    silence = AudioSegment.silent(duration=args.fade_time*3/4)
    generation = silence + generation + silence
    
    # crossfade intro and outro with generation
    final_audio = intro.append(generation, crossfade=args.fade_time).append(outro, crossfade=args.fade_time)
    
    # export final audio
    final_audio.export(args.output, format="mp3")
    
    

